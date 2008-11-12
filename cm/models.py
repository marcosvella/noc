from django.db import models
from django.db.models import Q
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.conf import settings
from noc.sa.profiles import profile_registry
from noc.setup.models import Settings
from noc.lib.url import URL
from noc.lib.fileutils import rewrite_when_differ,read_file,is_differ
from noc.lib.validators import is_int
from noc.cm.vcs import vcs_registry
import os,datetime,stat,logging,sets
from noc.sa.models import Activator
from noc.sa.protocols.sae_pb2 import TELNET,SSH,HTTP

profile_registry.register_all()
vcs_registry.register_all()

class ObjectCategory(models.Model):
    class Meta:
        verbose_name="Object Category"
        verbose_name_plural="Object Categories"
    name=models.CharField("Name",max_length=64,unique=True)
    description=models.CharField("Description",max_length=128,null=True,blank=True)
    def __unicode__(self):
        return self.name
        
class ObjectLocation(models.Model):
    class Meta:
        verbose_name="Object Location"
        verbose_name_plural="Object Locations"
    name=models.CharField("Name",max_length=64,unique=True)
    description=models.CharField("Description",max_length=128,null=True,blank=True)
    def __unicode__(self):
        return self.name
    @classmethod
    def default_location(cls):
        return cls.objects.order_by("id")[0]
#
OBJECT_TYPES=["config","dns","prefix-list","rpsl"]
OBJECT_TYPE_CHOICES=[(x,x) for x in OBJECT_TYPES]

class ObjectAccess(models.Model):
    class Meta:
        verbose_name="Object Access"
        verbose_name_plural="Object Access"
    type=models.CharField("Type",max_length=16,choices=OBJECT_TYPE_CHOICES)
    category=models.ForeignKey(ObjectCategory,verbose_name="Category",blank=True,null=True)
    location=models.ForeignKey(ObjectLocation,verbose_name="Location",blank=True,null=True)
    user=models.ForeignKey(User,verbose_name="User")
    def __unicode__(self):
        return "(%s,%s,%s,%s)"%(self.type,self.category,self.location,self.user)

class ObjectNotify(models.Model):
    class Meta:
        verbose_name="Object Notify"
        verbose_name_plural="Object Notifies"
    type=models.CharField("Type",max_length=16,choices=OBJECT_TYPE_CHOICES)
    category=models.ForeignKey(ObjectCategory,verbose_name="Category",blank=True,null=True)
    location=models.ForeignKey(ObjectLocation,verbose_name="Location",blank=True,null=True)
    emails=models.CharField("Emails",max_length=128)
    notify_immediately=models.BooleanField("Notify Immediately")
    notify_delayed=models.BooleanField("Notify Delayed")
    def __unicode__(self):
        return "(%s,%s,%s,%s)"%(self.type,self.category,self.location,self.emails)

#
class Object(models.Model):
    class Meta:
        abstract=True
    repo_path=models.CharField("Repo Path",max_length=128,unique=True)
    location=models.ForeignKey(ObjectLocation,verbose_name="Location")
    categories=models.ManyToManyField(ObjectCategory,verbose_name="Categories",null=True,blank=True)
    #
    last_modified=models.DateTimeField("Last Modified",blank=True,null=True)
    #
    push_every=models.PositiveIntegerField("Push Every (secs)",default=86400,blank=True,null=True)
    next_push=models.DateTimeField("Next Push",blank=True,null=True)
    last_push=models.DateTimeField("Last Push",blank=True,null=True)
    #
    pull_every=models.PositiveIntegerField("Pull Every (secs)",default=86400,blank=True,null=True)
    next_pull=models.DateTimeField("Next Pull",blank=True,null=True)
    last_pull=models.DateTimeField("Last Pull",blank=True,null=True) # Updated by write() method
    
    def __unicode__(self):
        return "%s/%s"%(self.repo_name,self.repo_path)
        
    def save(self,*args,**kwargs):
        mv=None
        if self._get_pk_val():
            old=self.__class__.objects.get(pk=self._get_pk_val())
            if old.repo_path!=self.repo_path:
                mv=(old.repo_path,self.repo_path)
        models.Model.save(self,*args,**kwargs)
        if mv:
            vcs=vcs_registry.get(self.repo)
            vcs.mv(mv[0],mv[1])
        
    def _repo(self):
        return os.path.join(Settings.get("cm.repo"),self.repo_name)
    repo=property(_repo)

    def _path(self):
        return os.path.join(self.repo,self.repo_path)
    path=property(_path)
    
    #
    # If "data" differs from object's content in the repository
    # Write "data" to file and commit
    #
    def write(self,data):
        path=self.path
        is_new=not os.path.exists(path)
        now=datetime.datetime.now()
        if rewrite_when_differ(self.path,data):
            vcs=vcs_registry.get(self.repo)
            if is_new:
                vcs.add(self.repo_path)
            vcs.commit(self.repo_path)
            self.last_modified=now
            self.on_object_changed()
        self.last_pull=now
        self.save()
    # Returns object's content
    # Or None if no content yet
    def _data(self):
        return read_file(self.path)
    data=property(_data)
    #
    def delete(self):
        vcs=vcs_registry.get(self.repo)
        vcs.rm(self.repo_path)
        super(Object,self).delete()

    def view_link(self):
        return "<A HREF='/cm/view/%s/%d/'>View</A>"%(self.repo_name,self.id)
    view_link.short_description="View"
    view_link.allow_tags=True

    def _revisions(self):
        vcs=vcs_registry.get(self.repo)
        return vcs.log(self.repo_path)
    revisions=property(_revisions)
    
    # Finds revision of the object and returns Revision
    def find_revision(self,rev):
        assert is_int(rev)
        for r in self.revisions:
            if r.revision==rev:
                return r
        raise Exception("Not found")
    
    def diff(self,rev1,rev2):
        vcs=vcs_registry.get(self.repo)
        return vcs.diff(self.repo_path,rev1,rev2)
        
    def get_revision(self,rev):
        vcs=vcs_registry.get(self.repo)
        return vcs.get_revision(self.repo_path,rev)
        
    @classmethod
    def get_object_class(self,repo):
        if repo=="config":
            return Config
        elif repo=="dns":
            return DNS
        elif repo=="prefix-list":
            return PrefixList
        elif repo=="rpsl":
            return RPSL
        else:
            raise Exception("Invalid repo '%s'"%repo)
    ##
    ## Access control
    ##
    def has_access(self,user):
        if user.is_superuser:
            return True
        return user.objectaccess_set.filter(
                    Q(type=self.repo_name)\
                    &(Q(location__isnull=True)|Q(location=self.location))\
                    &(Q(category__isnull=True)|Q(category__in=self.categories.all))
                    ).count()>0

    def can_change(self,user,location,categories):
        if user.is_superuser:
            return True
        if user.objectaccess_set.filter(
                Q(type=self.repo_name)\
                &(Q(location__isnull=True)|Q(location=self.location))\
                &Q(category__isnull=True)
                ).count()>0:
            return True
        if categories:
            for c in categories:
                if user.objectaccess_set.filter(
                        Q(type=self.repo_name)\
                        &(Q(location__isnull=True)|Q(location=self.location))\
                        &Q(category=c)
                        ).count()==0:
                    return False
            return True
        return False
        
    @classmethod
    def queryset(cls,user):
        # Idiotic implementation
        ids=[o.id for o in cls.objects.all() if o.has_access(user)]
        return cls.objects.filter(id__in=ids)
    
    def change_notify_list(self,immediately=False,delayed=False):
        emails=sets.Set()
        for n in ObjectNotify.objects.filter(Q(type=self.repo_name)\
                    &(Q(location__isnull=True)|Q(location=self.location))\
                    &(Q(category__isnull=True)|Q(category__in=self.categories.all))):
            if immediately and not n.notify_immediately:
                continue
            if delayed and not n.notify_delayed:
                continue
            emails.update(n.emails.split())
        return list(emails)
        
    def on_object_changed(self):
        emails=self.change_notify_list(immediately=True)
        if not emails:
            return
        revs=self.revisions
        now=datetime.datetime.now()
        if len(revs)==1:
            subject="NOC: Object '%s' was created"%str(self)
            message="The object %s was created at %s\n"%(str(self),now)
            message+="Object value follows:\n---------------------------\n%s\n-----------------------\n"%self.data
        else:
            subject="NOC: Object changed '%s'"%str(self)
            message="The object %s was changed at %s\n"%(str(self),now)
            message+="Object changes follows:\n---------------------------\n%s\n-----------------------\n"%self.diff(revs[-1],revs[0])
        send_mail(subject=subject,message=message,from_email=settings.SERVER_EMAIL,recipient_list=emails,fail_silently=True)
    ##
    ##
    def push(self): pass
    def pull(self): pass
    #
    # Push all objects of the given type
    #
    @classmethod
    def global_push(self): pass
    #
    # Pull all objects of the given type
    #
    @classmethod
    def global_pull(self): pass
##
## Config
##
class Config(Object):
    class Meta:
        verbose_name="Config"
        verbose_name_plural="Configs"
    activator=models.ForeignKey(Activator,verbose_name="Activator")
    profile_name=models.CharField("Profile",max_length=128,choices=profile_registry.choices)
    scheme=models.IntegerField("Scheme",choices=[(TELNET,"telnet"),(SSH,"ssh"),(HTTP,"http")])
    address=models.CharField("Address",max_length=64)
    port=models.PositiveIntegerField("Port",blank=True,null=True)
    user=models.CharField("User",max_length=32,blank=True,null=True)
    password=models.CharField("Password",max_length=32,blank=True,null=True)
    super_password=models.CharField("Super Password",max_length=32,blank=True,null=True)
    remote_path=models.CharField("Path",max_length=32,blank=True,null=True)
    
    repo_name="config"
    def _profile(self):
        return profile_registry[self.profile_name]()
    profile=property(_profile)
    
    def pull(self,sae):
        sae.pull_config(self)
##
## PrefixList
##
class PrefixList(Object):
    class Meta:
        verbose_name="Prefix List"
        verbose_name_plural="Prefix Lists"
    repo_name="prefix-list"
    @classmethod
    def global_pull(cls):
        from noc.peer.builder import build_prefix_lists
        location=ObjectLocation.default_location()
        objects={}
        for o in PrefixList.objects.all():
            objects[o.repo_path]=o
        logging.debug("PrefixList.global_pull(): building prefix lists")
        for peering_point,pl_name,pl in build_prefix_lists():
            logging.debug("PrefixList.global_pull(): writing %s/%s (%d lines)"%(peering_point.hostname,pl_name,len(pl.split("\n"))))
            path=os.path.join(peering_point.hostname,pl_name)
            if path in objects:
                o=objects[path]
                del objects[path]
            else:
                o=PrefixList(repo_path=path,location=location)
                o.save()
            o.write(pl)
        for o in objects.values():
            o.delete()
##
## DNS
##
class DNS(Object):
    class Meta:
        verbose_name="DNS Object"
        verbose_name_plural="DNS Objects"
    repo_name="dns"
    @classmethod
    def global_pull(cls):
        from noc.dns.models import DNSZone,DNSServer
        
        location=ObjectLocation.default_location()
        objects={}
        changed={}
        for o in DNS.objects.exclude(repo_path__endswith="autozones.conf"):
            objects[o.repo_path]=o
        for z in DNSZone.objects.filter(is_auto_generated=True):
            for ns in z.profile.masters.all():
                path=os.path.join(ns.name,z.name)
                if path in objects:
                    o=objects[path]
                    del objects[path]
                else:
                    logging.debug("DNSHandler.global_pull: Creating object %s"%path)
                    o=DNS(repo_path=path,location=location)
                    o.save()
                if is_differ(o.path,z.zonedata(ns)):
                    changed[z]=None
        for o in objects.values():
            logging.debug("DNS.global_pull: Deleting object: %s"%o.repo_path)
            o.delete()
        for z in changed:
            logging.debug("DNS.global_pull: Zone %s changed"%z.name)
            z.serial=z.next_serial
            z.save()
            for ns in z.profile.masters.all():
                path=os.path.join(ns.name,z.name)
                o=DNS.objects.get(repo_path=path)
                o.write(z.zonedata(ns))
        for ns in DNSServer.objects.all():
            logging.debug("DNSHandler.global_pull: Includes for %s rebuilded"%ns.name)
            g=ns.generator_class()
            path=os.path.join(ns.name,"autozones.conf")
            try:
                o=DNS.objects.get(repo_path=path)
            except Object.DoesNotExist:
                o=DNS(repo_path=path)
                o.save()
            o.write(g.get_include(ns))
            
    @classmethod
    def global_push(self):
        from noc.dns.models import DNSZone
        nses={}
        for z in DNSZone.objects.filter(is_auto_generated=True):
            for ns in z.profile.masters.all():
                nses[ns.name]=ns
        for ns in nses.values():
            logging.debug("DNSHandler.global_push: provisioning %s"%ns.name)
            ns.provision_zones()
##
## RPSL
##
class RPSL(Object):
    class Meta:
        verbose_name="RPSL Object"
        verbose_name_plural="RPSL Objects"
    repo_name="rpsl"
    @classmethod
    def global_pull(cls):
        def global_pull_class(name,c,name_fun):
            location=ObjectLocation.default_location()
            objects={}
            for o in RPSL.objects.filter(repo_path__startswith=name+os.sep):
                objects[o.repo_path]=o
            for a in c.objects.all():
                path=os.path.join(name,name_fun(a))
                if path in objects:
                    o=objects[path]
                    del objects[path]
                else:
                    o=RPSL(repo_path=path,location=location)
                    o.save()
                o.write(a.rpsl)
            for o in objects.values():
                o.delete()
        from noc.peer.models import AS,ASSet
        logging.debug("RPSL.global_pull(): building RPSL")
        global_pull_class("as",AS,lambda a:"AS%d"%a.asn)
        global_pull_class("as-set",ASSet,lambda a:a.name)
    
    @classmethod
    def global_push(cls): pass
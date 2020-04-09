# -*- coding: utf-8 -*-
# ---------------------------------------------------------------------
# "now"search"" macro
# ---------------------------------------------------------------------
# Copyright (C) 2007-2019 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Third-party modules
from django.db.models import Q
from .base import BaseMacro


class SearchMacro(BaseMacro):
    """
    *search* macro
    USAGE:
    <<search [criteria] [order_by] [limit] [title]>>
    WHERE:
        criteria:
            tags=tag1,...,tagN
            language=lang
        order_by - one of "subject","-subject","id","-id"
        limit
        title - table title
        display_list - list of fields ("id","subject")
    """

    name = "search"

    @classmethod
    def handle(cls, args, text):
        from noc.kb.models.kbentry import KBEntry

        # Build search criteria
        q = Q()
        if "tags" in args:
            tags = args["tags"].split(",")
            tags = [x for x in tags if x]
            if tags:
                q &= Q(tags__contains=tags)
        if "language" in args:
            q &= Q(language__name=args["language"])
        q = KBEntry.objects.filter(q)  # Flatten to query
        # Apply ordering
        if "order_by" in args:
            if args["order_by"] not in ["subject", "-subject", "id", "-id"]:
                raise Exception("Invalid order_by value")
            q = q.order_by(args["order_by"])
        # Apply limition
        if "limit" in args:
            q = q[: int(args["limit"])]
        # Build display list
        if "display_list" in args:
            display_list = []
            for f in args["display_list"].split(","):
                f = f.strip()
                if f not in ("id", "subject"):
                    raise Exception("Invalid field %s" % f)
                display_list.append(f)
        else:
            display_list = ["id", "subject"]
        # Render
        out = ["<table border='0'>"]
        if "title" in args:
            out += ["<tr><th>%s</th></tr>" % args["title"]]
        for a in q:
            link = "/api/card/view/kb/%d/" % a.id
            out += ["<tr>"]
            for f in display_list:
                if f == "id":
                    out += ["<td><a href='%s'>KB%s</a></td>" % (link, getattr(a, f))]
                else:
                    out += ["<td><a href='%s'>%s</a></td>" % (link, getattr(a, f))]
            out += ["</tr>"]
        out += ["</table>"]
        return "\n".join(out)

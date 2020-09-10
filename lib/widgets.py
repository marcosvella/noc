# ---------------------------------------------------------------------
# Form widgets
# ---------------------------------------------------------------------
# Copyright (C) 2007-2020 The NOC Project
# See LICENSE for details
# ---------------------------------------------------------------------

# Third-party modules
from django.forms.widgets import Input
from django.http import HttpResponse
from django.utils.safestring import mark_safe
import orjson

# NOC modules
from noc.core.comp import smart_text


class AutoCompleteTags(Input):
    input_type = "text"

    class Media(object):
        css = {"all": ["/ui/pkg/jquery.tokeninput/jquery.tokeninput.css"]}
        js = ["/ui/pkg/jquery.tokeninput/jquery.tokeninput.js"]

    def render(self, name, value=None, attrs=None):
        initial = []
        if value:
            for v in [x for x in value.split(",") if x]:
                v = v.strip()
                if v:
                    initial += [{"id": v, "name": v}]
        initial = smart_text(orjson.dumps(initial))
        html = super().render(name, value, attrs)
        js = """<script type="text/javascript">
        $(document).ready(function() {
            $("#%s").tokenInput("%s",{
                prePopulate: %s,
                allowNewValues: true,
                canCreate: true,
                queryParam: "query",
                classes: {
                    tokenList: "token-input-list-noc",
                    token: "token-input-token-noc",
                    tokenDelete: "token-input-delete-token-noc",
                    selectedToken: "token-input-selected-token-noc",
                    highlightedToken: "token-input-highlighted-token-noc",
                    dropdown: "token-input-dropdown-noc",
                    dropdownItem: "token-input-dropdown-item-noc",
                    dropdownItem2: "token-input-dropdown-item2-noc",
                    selectedDropdownItem: "token-input-selected-dropdown-item-noc",
                    inputToken: "token-input-input-token-noc"
                },
                onResult: function (results) {
                    return results.data.map(function(item) {
                                return {id: item.id, name: item.label}
                            });
                }
                });
            });
        </script>
        """ % (
            attrs["id"],
            "/main/tag/ac_lookup/",
            initial,
        )
        return mark_safe("\n".join([html, js]))


def lookup(request, func):
    result = []
    if request.GET and "query" in request.GET:
        q = request.GET["query"]
        if len(q) > 2:  # Ignore requests shorter than 3 letters
            result = list(func(q))
    return HttpResponse("\n".join(result), content_type="text/plain")


def tags_list(o):
    if isinstance(o.tags, str):
        tags = [x for x in o.tags.split(",") if x]
    else:
        tags = o.tags or []
    s = ["<ul class='tags-list'>"] + ["<li>%s</li>" % t for t in tags] + ["</ul>"]
    return "".join(s)

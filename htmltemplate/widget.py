from .elem import *

def mat_select(id, label, options, name=None, multiple=False, mobile=False, classes=[], optionsClasses=[], placeholder=None):
    lbl=htmllabel(label)
    select=htmlselect(id=id)
    select.add_class(classes)
    if mobile: select.add_class("browser-default")
    if multiple: select.attrs["multiple"]=None
    if name: select.attrs["name"]=name
    if placeholder: select.attrs["placeholder"]=placeholder
    for k in options:
        oa={"value" : k}
        select.append(htmloption(options[k], classes=optionsClasses, attrs=oa))
    return lbl.after(select)

def mat_input_text(id, label, type="text", value="", disable=False, name=""):
    lbl=htmllabel(value, attrs={"for" : id})
    input=html_input(id, type, ["validate"], attrs={
        "placehoder" : label,
        "disabled" if disable else "": None,
        "name": name
    })
    return  htmldiv([input, lbl], classes="input-field")

def mat_switch(id, labelOn, labelOff="", name=""):
    if name: input=html_input(id, "checkbox", attrs={ "name": name}).after(htmlspan(classes="lever"))
    else: input=html_input(id, "checkbox").after(htmlspan(classes="lever"))

    return  htmldiv(htmllabel([ labelOn, input, labelOff]), classes="switch")

def mat_row(content, classes="col s12", id=None):
    if isinstance(content, (list, tuple)): content="\n".join(content)
    x=htmldiv(content, classes="row ", id=id)
    return  x.add_class(classes)

def mat_col(content, classes="s12"):
    if isinstance(content, (list, tuple)): content="\n".join(content)
    x=htmldiv(content, classes="col ")
    return  x.add_class(classes)


def mat_pagination(n, size, link, nexts=3):
    out='<ul class="pagination center-align">'
    if n==0: out+='<li class="disabled"><i class="material-icons">chevron_left</i></li>'
    else: out+='<li class="waves-effect"><a href="'+link.replace("{}", str(n+1))+'"><i class="material-icons">chevron_left</i></a></li>'

    if n-nexts>0: out+='<li class="waves-effect">...</li>'
    for i in range(n-nexts, n+nexts):
        if i>=0 and i<size:
            out+='<li class="'
            out+= 'active"' if i==n else 'waves-effect"'
            out+='><a href="'+link.replace("{}", str(i+1))+'">'+str(i+1)+'</a></li>'

    if n+nexts<size: out+='<li class="waves-effect">...</li>'


    if n == size-1:
        out += '<li class="disabled"><i class="material-icons">chevron_right</i></li>'
    else:
        out += '<li class="waves-effect"><a href="'+link.replace("{}", str(n+2))+'"><i class="material-icons">chevron_right</i></a></li>'

    out+='</ul>'
    return out
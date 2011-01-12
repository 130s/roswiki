import urllib2
from MoinMoin.Page import Page
from MoinMoin.wikiutil import get_unicode

from macroutils import wiki_url, get_repo_li, get_vcs_li, load_stack_release, msg_doc_link, load_package_manifest, package_html_link, UtilException

generates_headings = True
dependencies = []

def macro_PackageHeader(macro, arg1, arg2='en'):
  package_name = get_unicode(macro.request, arg1)
  lang = get_unicode(macro.request, arg2)
  if not package_name:
    return "ERROR in PackageHeader. Usage: [[PackageHeader(pkg_name opt_lang)]]"    
  package_url = package_html_link(package_name)
  try:
      data = load_package_manifest(package_name, lang)
  except UtilException, e:
      return str(e)

  # keys
  brief = data.get('brief', package_name)
  authors = data.get('authors', 'unknown')
  try:
    if type(authors) != unicode:
      authors = unicode(authors, 'utf-8')
  except UnicodeDecodeError:
    authors = ''
  license = data.get('license', 'unknown')
  description = data.get('description', '')
  try:
    if type(description) != unicode:
      description = unicode(description, 'utf-8')
  except UnicodeDecodeError:
    description = ''
  depends = data.get('depends', [])
  depends_on = data.get('depends_on', [])
  review_status = data.get('review_status', 'unreviewed')
  review_notes = data.get('review_notes', '') or ''
  external_documentation = data.get('external_documentation', '') or data.get('url', '') or '' 
  if 'ros.org' in external_documentation or 'pr.willowgarage.com' in external_documentation:
     external_documentation = u''
  api_documentation = data.get('api_documentation', '')

  f = macro.formatter
  p, url, div = f.paragraph, f.url, f.div
  em, strong, br = f.emphasis, f.strong, f.linebreak
  li, ul = f.listitem, f.bullet_list
  h = f.heading
  text, rawHTML = f.text, f.rawHTML
  comment = f.comment

  if stack and stack.lower() not in ['sandbox']:
    # set() logic is to get around temporary bug
    siblings = list(set(data.get('siblings', [])))
    # filter out test packages
    siblings = [s for s in siblings if not s.startswith('test_')]
    siblings.sort()
    pagename = macro.formatter.page.page_name

    if stack == pagename:
      top = strong(1)+text(stack)+strong(0)
    else:
      top = strong(1)+wiki_url(macro, stack)+strong(0)+text(': ')

    parts = []
    for s in siblings:
      if s == pagename:
        parts.append(text(s))
      else:
        parts.append(wiki_url(macro, s))
    #nav = em(1) + top + ' | '.join(parts) + em(0)
    nav = em(1) + top
    if parts: 
      nav += parts[0]
      for part in parts[1:]:
        nav += text(' | ')+part
    nav += em(0)
  elif stack and stack.lower() == 'sandbox':
    nav = strong(1)+wiki_url(macro, stack)+strong(0)
  else:
    nav = text('')
  nav += '<script type="text/javascript" src="/js/roswiki.js"></script>'
  
  # - package data keys
  msgs = data.get('msgs', [])
  srvs = data.get('srvs', [])

  # - package links
  #   -- link to msg/srv autogenerated docs
  msg_doc_title = "Msg/Srv API"
  if msgs and not srvs:
    msg_doc_title = "Msg API"
  elif srvs and not msgs:
    msg_doc_title = "Srv API"
  if msgs or srvs:
    msg_doc = li(1)+strong(1)+msg_doc_link(package_name, msg_doc_title)+strong(0)+li(0)
  else:
    msg_doc = text('')

  troubleshooting = Page(macro.request, '%s/Troubleshooting'%package_name).link_to(macro.request, text='Troubleshooting')
  tutorials = Page(macro.request, '%s/Tutorials'%package_name).link_to(macro.request, text='Tutorials')
  review_link = Page(macro.request, '%s/Reviews'%package_name).link_to(macro.request, text='Reviews')
  review_str = '%(review_link)s (%(review_status)s)'%locals()
  dependency_tree = data.get('dependency_tree', '')
  if external_documentation:
    external_documentation = li(1)+strong(1)+url(1, url=external_documentation)+text("External Documentation")+url(0)+strong(0)+li(0)
  
  try:
    repo_li = get_repo_li(macro, data)
    vcs_li = get_vcs_li(macro, data)

    package_desc = h(1, 2, id="first")+text('Package Summary')+h(0, 2)+\
      p(1, css_id="package-info")+rawHTML(description)+p(0)+\
      p(1, id="package-info")+\
      ul(1)+li(1)+text("Author: %s"%authors)+li(0)+\
      li(1)+text("License: %s"%license)+li(0)+\
      repo_li+\
      vcs_li+\
      ul(0)+p(0)

  except UnicodeDecodeError:
    package_desc = h(1, 2)+text('Package Summary')+h(0, 2)+\
      p(1)+text('Error retrieving package summary')+p(0)

  try:
    package_links = div(1, css_class="package-links")+\
      strong(1)+text("Package Links")+strong(0)+\
      ul(1)+\
      li(1)+strong(1)+url(1, url=package_url)+text("Code API")+url(0)+strong(0)+li(0)+msg_doc+\
      external_documentation+\
      li(1)+tutorials+li(0)+\
      li(1)+troubleshooting+li(0)+\
      li(1)+review_str+li(0)+\
      li(1)+url(1, url=dependency_tree)+text('Dependency Tree')+url(0)+li(0)+\
      ul(0)
  except UnicodeDecodeError:
    package_links = div(1, css_class="package-links")+div(0)

  if depends:
    depends.sort()

    package_links += strong(1)+'<a href="#" onClick="toggleExpandable(\'dependencies-list\');">Dependencies</a> (%s)'%(len(depends))+strong(0)+'<br />\n<div id="dependencies-list" style="display:none">'+ul(1)
    for d in depends:
      package_links += li(1)+wiki_url(macro,d,shorten=20)+li(0)
    package_links += ul(0)+div(0)

  if depends_on:
    depends_on.sort()
    d_links =  u'\n'.join([u"<li>%s</li>"%wiki_url(macro,d,shorten=20) for d in depends_on]) 
    package_links += strong(1)+'<a href="#" onClick="toggleExpandable(\'used-by-list\');">Used by</a> (%s)'%(len(depends_on))+strong(0)+\
      '<br />\n<div id="used-by-list" style="display:none">'+\
      ul(1)+rawHTML(d_links)+ul(0)+\
      div(0)

  package_links+=div(0)
  return rawHTML(nav) + package_links + package_desc 


# This code is in Public Domain. Take all the code you want, I'll just write more.
import os, string, Cookie, sha, time, random, cgi, urllib, datetime, StringIO, pickle
import wsgiref.handlers
from google.appengine.api import users
#from google.appengine.api import memcache
from models.models import MemcacheManager as memcache
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
import logging
from offsets import *
from markupsafe import Markup

from models.models import Student
from controllers.utils import BaseHandler
import controllers.sites
import humanize
import bleach

# Structure of urls:
#
# Top-level urls
#
# / - list of all forums
#
# /manageforums[?forum=<key> - edit/create/disable forums
#
# Per-forum urls
#
# /<forum_url>/[?from=<n>]
#    index, lists of topics, optionally starting from topic <n>
#
# /<forum_url>/post[?id=<id>]
#    form for creating a new post. if "topic" is present, it's a post in
#    existing topic, otherwise a post starting a new topic
#
# /<forum_url>/topic?id=<id>&comments=<comments>
#    shows posts in a given topic, 'comments' is ignored (just a trick to re-use
#    browser's history to see if the topic has posts that user didn't see yet
#
# /<forum_url>/postdel?<post_id>
# /<forum_url>/postundel?<post_id>
#    delete/undelete post
#
# /<forum_url>/rss
#    rss feed for first post in the topic (default)
#
# /<forum_url>/rssall
#    rss feed for all posts

# HTTP codes
HTTP_NOT_ACCEPTABLE = 406
HTTP_NOT_FOUND = 404

FORUMS_MEMCACHE_KEY = "fo"
MAX_FORUMS = 256 # if you need more, tough

FORUMS_ROOT = "/forum"

def rss_memcache_key(forum):
    return "rss" + str(forum.key().id())

def topics_memcache_key(forum):
  return "to" + str(forum.key().id())

BANNED_IPS = {
    "59.181.121.8"  : 1,
    "62.162.98.194" : 1,
    "93.191.0.129"  : 1,
    "31.31.26.59"   : 1,
    "37.26.132.20"  : 1,
    "31.31.26.198"  : 1
    #"127.0.0.1" : 1,
}

def my_hostname():
    # TODO: handle https as well
    h = "http://" + os.environ["SERVER_NAME"];
    port = os.environ["SERVER_PORT"]
    if port != "80":
        h += ":%s" % port
    return h

class Forum(db.Model):
  # Urls for forums are in the form /<urlpart>/<rest>
  url = db.StringProperty(required=True)
  # What we show as html <title> and as main header on the page
  title = db.StringProperty()
  # a tagline is below title
  tagline = db.StringProperty()
  # stuff to display in left sidebar
  sidebar = db.TextProperty()
  # if true, forum has been disabled. We don't support deletion so that
  # forum can always be re-enabled in the future
  is_disabled = db.BooleanProperty(default=False)
  # just in case, when the forum was created. Not used.
  created_on = db.DateTimeProperty(auto_now_add=True)
  # name of the skin (must be one of SKINS)
  skin = db.StringProperty()
  # Google analytics code
  analytics_code = db.StringProperty()
  # Note: import_secret is obsolete
  import_secret = db.StringProperty()

  @property
  def title_or_url(self):
      return self.title or self.url

# A forum is collection of topics
class Topic(db.Model):
  forum = db.Reference(Forum, required=True)
  subject = db.StringProperty(required=True)
  created_on = db.DateTimeProperty(auto_now_add=True)
  # name of person who created the topic. Duplicates Post.user_name
  # of the first post in this topic, for speed
  created_by = db.StringProperty()
  # just in case, not used
  updated_on = db.DateTimeProperty(auto_now=True)
  # True if first Post in this topic is deleted. Updated on deletion/undeletion
  # of the post
  is_deleted = db.BooleanProperty(default=False)
  # ncomments is redundant but is faster than always quering count of Posts
  ncomments = db.IntegerProperty(default=0)

# A topic is a collection of posts
class Post(db.Model):
  topic = db.Reference(Topic, required=True)
  forum = db.Reference(Forum, required=True)
  created_on = db.DateTimeProperty(auto_now_add=True)
  message = db.TextProperty(required=True)
  sha1_digest = db.StringProperty(required=True)
  # admin can delete/undelete posts. If first post in a topic is deleted,
  # that means the topic is deleted as well
  is_deleted = db.BooleanProperty(default=False)
  # ip address from which this post has been made
  user_ip_str = db.StringProperty(required=False)
  # user_ip is an obsolete value, only used for compat with entries created before
  # we introduced user_ip_str. If it's 0, we assume we'll use user_ip_str, otherwise
  # we'll user user_ip
  user_ip = db.IntegerProperty(required=True)

  user = db.Reference(Student, required=True)
  # user_name, user_email and user_homepage might be different than
  # name/homepage/email fields in user object, since they can be changed in
  # FofouUser
  user_name = db.StringProperty()
  user_email = db.StringProperty()
  user_homepage = db.StringProperty()

SKINS = ["default"]

# cookie code based on http://code.google.com/p/appengine-utitlies/source/browse/trunk/utilities/session.py
FOFOU_COOKIE = "fofou-uid"
COOKIE_EXPIRE_TIME = 60*60*24*120 # valid for 60*60*24*120 seconds => 120 days

def get_user_agent(): return os.environ['HTTP_USER_AGENT']
def get_remote_ip(): return os.environ['REMOTE_ADDR']

def long2ip(val):
  slist = []
  for x in range(0,4):
    slist.append(str(int(val >> (24 - (x * 8)) & 0xFF)))
  return ".".join(slist)

def to_unicode(val):
  if isinstance(val, unicode): return val
  try:
    return unicode(val, 'latin-1')
  except:
    pass
  try:
    return unicode(val, 'ascii')
  except:
    pass
  try:
    return unicode(val, 'utf-8')
  except:
    raise

def to_utf8(s):
    s = to_unicode(s)
    return s.encode("utf-8")

def req_get_vals(req, names, strip=True):
  if strip:
    return [req.get(name).strip() for name in names]
  else:
    return [req.get(name) for name in names]

def get_inbound_cookie():
  c = Cookie.SimpleCookie()
  cstr = os.environ.get('HTTP_COOKIE', '')
  c.load(cstr)
  return c

def new_user_id():
  sid = sha.new(repr(time.time())).hexdigest()
  return sid

def valid_user_cookie(c):
  # cookie should always be a hex-encoded sha1 checksum
  if len(c) != 40:
    return False
  # TODO: check that user with that cookie exists, the way appengine-utilities does
  return True

g_anonUser = None
def anonUser():
  global g_anonUser
  if None == g_anonUser:
    g_anonUser = users.User("dummy@dummy.address.com")
  return g_anonUser

def fake_error(response):
  response.headers['Content-Type'] = 'text/plain'
  response.out.write('There was an error processing your request.')

def valid_forum_url(url):
  if not url:
    return False
  try:
    return url == urllib.quote_plus(url)
  except:
    return False

# very simplistic check for <txt> being a valid e-mail address
def valid_email(txt):
  # allow empty strings
  if not txt:
    return True
  if '@' not in txt:
    return False
  if '.' not in txt:
    return False
  return True

def forum_root(forum): return "/forum/" + forum.url + "/"

def clear_forums_memcache():
  memcache.delete(FORUMS_MEMCACHE_KEY)

def clear_topics_memcache(forum):
  memcache.delete(topics_memcache_key(forum))

def get_forum_by_url(forumurl):
  # number of forums is small, so we cache all of them
  forums = memcache.get(FORUMS_MEMCACHE_KEY)
  if not forums:
    forums = Forum.all().fetch(200) # this effectively limits number of forums to 200
    if not forums:
      return None

    memcache.set(FORUMS_MEMCACHE_KEY, forums)
  for forum in forums:
    if forumurl == forum.url:
      return forum
  return None

def forum_siteroot_tmpldir_from_url(url):
  assert '/' == url[0]
  path = url[len('/forum/'):]
  if '/' in path:
    (forumurl, rest) = path.split("/", 1)
  else:
    forumurl = path
  forum = get_forum_by_url(forumurl)
  if not forum:
    return (None, None, None)
  siteroot = forum_root(forum)
  skin_name = forum.skin
  if skin_name not in SKINS:
    skin_name = SKINS[0]
  tmpldir = os.path.join("skins", skin_name)
  return (forum, siteroot, tmpldir)

def get_log_in_out(url):
  user = users.get_current_user()
  if user:
    if users.is_current_user_admin():
      return Markup("Welcome admin, %s! <a href=\"%s\">Log out</a>") % (user.nickname(), users.create_logout_url(url))
    else:
      return Markup("Welcome, %s! <a href=\"%s\">Log out</a>") % (user.nickname(), users.create_logout_url(url))
  else:
    return Markup("<a href=\"%s\">Log in or register</a>") % users.create_login_url(url)

def linebreaksbr(s):
    return s.replace("\n", Markup("<br>"))

def pluralize(n, suffix="s"):
    return suffix if n != 1 else ''

def better_striptags(s):
    return bleach.clean(s,
            tags=[],
            strip=True)

class FofouBase(BaseHandler):
  def __init__(self, *args, **kwargs):
    self.app_context = controllers.sites.get_all_courses()[0]
    super(FofouBase, self).__init__(*args, **kwargs)
    self.template_value['navbar'] = {'forum': True}

  _cookie = None
  # returns either a FOFOU_COOKIE sent by the browser or a newly created cookie
  def get_cookie(self):
    if self._cookie != None:
      return self._cookie
    cookies = get_inbound_cookie()
    for cookieName in cookies.keys():
      if FOFOU_COOKIE != cookieName:
        del cookies[cookieName]
    if (FOFOU_COOKIE not in cookies) or not valid_user_cookie(cookies[FOFOU_COOKIE].value):
      cookies[FOFOU_COOKIE] = new_user_id()
      cookies[FOFOU_COOKIE]['path'] = '/'
      cookies[FOFOU_COOKIE]['expires'] = COOKIE_EXPIRE_TIME
    self._cookie = cookies[FOFOU_COOKIE]
    return self._cookie

  _cookie_to_set = None
  # remember cookie so that we can send it when we render a template
  def send_cookie(self):
    if None == self._cookie_to_set:
      self._cookie_to_set = self.get_cookie()

  def get_cookie_val(self):
    c = self.get_cookie()
    return c.value

  def mess_with_template_environ(self, environ):
    environ.filters['linebreaksbr'] = linebreaksbr
    environ.filters['date'] = humanize.naturaltime
    environ.filters['pluralize'] = pluralize
    environ.filters['striptags'] = better_striptags

  def template_out(self, template_name, template_values):
    """Renders a template."""
    self.response.headers['Content-Type'] = 'text/html'
    if None != self._cookie_to_set:
      # a hack extract the cookie part from the whole "Set-Cookie: val" header
      c = str(self._cookie_to_set)
      c = c.split(": ", 1)[1]
      self.response.headers["Set-Cookie"] = c
    #path = os.path.join(os.path.dirname(__file__), template_name)
    path = template_name
    template = self.get_template(path, additional_dirs=[os.path.dirname(__file__)])
    template_values.update(self.template_value)
    self.response.out.write(template.render(template_values))


  #def redirect(self, where):
    #super(FofouBase, self).redirect("/forum" + where)

# responds to GET /manageforums[?forum=<key>&disable=yes&enable=yes]
# and POST /manageforums with values from the form
class ManageForums(FofouBase):

  def post(self):
    if not users.is_current_user_admin():
      return self.redirect(FORUMS_ROOT + "/")

    forum_key = self.request.get('forum_key')
    forum = None
    if forum_key:
      forum = db.get(db.Key(forum_key))
      if not forum:
        # invalid key - should not happen so go to top-level
        return self.redirect(FORUMS_ROOT + "/")

    vals = ['url','title', 'tagline', 'sidebar', 'disable', 'enable', 'analyticscode']
    (url, title, tagline, sidebar, disable, enable, analytics_code) = req_get_vals(self.request, vals)

    errmsg = None
    if not valid_forum_url(url):
      errmsg = "Url contains illegal characters"
    if not forum:
      forum_exists = Forum.gql("WHERE url = :1", url).get()
      if forum_exists:
        errmsg = "Forum with this url already exists"

    if errmsg:
      tvals = {
        'urlclass' : "error",
        'hosturl' : self.request.host_url,
        'prevurl' : url,
        'prevtitle' : title,
        'prevtagline' : tagline,
        'prevsidebar' : sidebar,
        'prevanalyticscode' : analytics_code,
        'forum_key' : forum_key,
        'errmsg' : errmsg
      }
      return self.render_rest(tvals)

    clear_forums_memcache()
    title_or_url = title or url
    if forum:
      # update existing forum
      forum.url = url
      forum.title = title
      forum.tagline = tagline
      forum.sidebar = sidebar
      forum.analytics_code = analytics_code
      forum.put()
      msg = "Forum '%s' has been updated." % title_or_url
    else:
      # create a new forum
      forum = Forum(url=url, title=title, tagline=tagline, sidebar=sidebar, analytics_code = analytics_code)
      forum.put()
      msg = "Forum '%s' has been created." % title_or_url
    url = "/manageforums?msg=%s" % urllib.quote(to_utf8(msg))
    return self.redirect(FORUMS_ROOT + url)

  def get(self, *args):
    if not self.personalize_page_and_get_enrolled():
      return
    if not users.is_current_user_admin():
      return self.redirect(FORUMS_ROOT + "/")

    # if there is 'forum_key' argument, this is editing an existing forum.
    forum = None
    forum_key = self.request.get('forum_key')
    if forum_key:
      forum = db.get(db.Key(forum_key))
      if not forum:
        # invalid forum key - should not happen, return to top level
        return self.redirect(FORUMS_ROOT + "/")

    tvals = {
      'hosturl' : self.request.host_url,
      'forum' : forum
    }
    if forum:
      forum.title_non_empty = forum.title or "Title."
      forum.sidebar_non_empty = forum.sidebar or "Sidebar."
      disable = self.request.get('disable')
      enable = self.request.get('enable')
      if disable or enable:
        title_or_url = forum.title or forum.url
        if disable:
          forum.is_disabled = True
          forum.put()
          msg = "Forum %s has been disabled." % title_or_url
        else:
          forum.is_disabled = False
          forum.put()
          msg = "Forum %s has been enabled." % title_or_url
        return self.redirect(FORUMS_ROOT + "/manageforums?msg=%s" % urllib.quote(to_utf8(msg)))
    self.render_rest(tvals, forum)

  def render_rest(self, tvals, forum=None):
    user = users.get_current_user()
    forumsq = db.GqlQuery("SELECT * FROM Forum")
    forums = []
    for f in forumsq:
      edit_url = FORUMS_ROOT + "/manageforums?forum_key=" + str(f.key())
      if f.is_disabled:
        f.enable_disable_txt = "enable"
        f.enable_disable_url = edit_url + "&enable=yes"
      else:
        f.enable_disable_txt = "disable"
        f.enable_disable_url = edit_url + "&disable=yes"
      if forum and f.key() == forum.key():
        # editing existing forum
        f.no_edit_link = True
        tvals['prevurl'] = f.url
        tvals['prevtitle'] = f.title
        tvals['prevtagline'] = f.tagline
        tvals['prevsidebar'] = f.sidebar
        tvals['prevanalyticscode'] = f.analytics_code
        tvals['forum_key'] = str(f.key())
      forums.append(f)
    tvals['msg'] = self.request.get('msg')
    tvals['user'] = user
    tvals['forums'] = forums
    if forum and not forum.tagline:
      forum.tagline = "Tagline."
    self.template_out("manage_forums.html", tvals)

# responds to /, shows list of available forums or redirects to
# forum management page if user is admin
class ForumList(FofouBase):
  def get(self):
    if not self.personalize_page_and_get_enrolled():
      return
    if users.is_current_user_admin():
      return self.redirect(FORUMS_ROOT + "/manageforums")
    forums = db.GqlQuery("SELECT * FROM Forum where is_disabled = False").fetch(MAX_FORUMS)
    tvals = {
      'forums' : forums,
      'isadmin' : users.is_current_user_admin(),
      'log_in_out' : get_log_in_out(self.request.uri)
    }
    self.template_out("forum_list.html", tvals)
    return None

# responds to GET /postdel?<post_id> and /postundel?<post_id>
class PostDelUndel(webapp.RequestHandler):
  def get(self, *args):
    (forum, siteroot, tmpldir) = forum_siteroot_tmpldir_from_url(self.request.path_info)
    if not forum or forum.is_disabled:
      return self.redirect(FORUMS_ROOT + "/")
    is_moderator = users.is_current_user_admin()
    if not is_moderator or forum.is_disabled:
      return self.redirect(siteroot)
    post_id = self.request.query_string
    #logging.info("PostDelUndel: post_id='%s'" % post_id)
    post = db.get(db.Key.from_path('Post', int(post_id)))
    if not post:
      logging.info("No post with post_id='%s'" % post_id)
      return self.redirect(siteroot)
    if post.forum.key() != forum.key():
      loggin.info("post.forum.key().id() ('%s') != fourm.key().id() ('%s')" % (str(post.forum.key().id()), str(forum.key().id())))
      return self.redirect(siteroot)
    path = self.request.path
    if path.endswith("/postdel"):
      if not post.is_deleted:
        post.is_deleted = True
        post.put()
        memcache.delete(rss_memcache_key(forum))
      else:
        logging.info("Post '%s' is already deleted" % post_id)
    elif path.endswith("/postundel"):
      if post.is_deleted:
        post.is_deleted = False
        post.put()
        memcache.delete(rss_memcache_key(forum))
      else:
        logging.info("Trying to undelete post '%s' that is not deleted" % post_id)
    else:
      logging.info("'%s' is not a valid path" % path)

    topic = post.topic
    # deleting/undeleting first post also means deleting/undeleting the whole topic
    first_post = Post.gql("WHERE forum=:1 AND topic = :2 ORDER BY created_on", forum, topic).get()
    if first_post.key() == post.key():
      if path.endswith("/postdel"):
        topic.is_deleted = True
      else:
        topic.is_deleted = False
      topic.put()
      clear_topics_memcache(forum)

    # redirect to topic owning this post
    topic_url = siteroot + "topic?id=" + str(topic.key().id())
    self.redirect(topic_url)

# returns (topics, new_off)
def get_topics_for_forum(forum, is_moderator, off, count):
  off = int(off)
  key = topics_memcache_key(forum)
  topics = memcache.get(key)
  if not topics:
    q = Topic.gql("WHERE forum = :1 ORDER BY created_on DESC", forum)
    topics = q.fetch(1000)
    if topics:
      #memcache.set(key, topics) # TODO: should I pickle?
      pass # Not caching this for now :(
  if not topics:
    return (None, 0)
  if topics and not is_moderator:
    topics = [t for t in topics if not t.is_deleted]
  topics = topics[off:off+count]
  new_off = off + len(topics)
  if len(topics) < count:
    new_off = None # signal this is the last page
  return (topics, new_off)

# responds to /<forumurl>/[?from=<from>]
# shows a list of topics, potentially starting from topic N
class TopicList(FofouBase):

  def get(self, forum):
    if not self.personalize_page_and_get_enrolled():
      return
    (forum, siteroot, tmpldir) = forum_siteroot_tmpldir_from_url(self.request.path_info)
    if not forum or forum.is_disabled:
      return self.redirect(FORUMS_ROOT + "/")
    off = self.request.get("from") or 0
    is_moderator = users.is_current_user_admin()
    MAX_TOPICS = 75
    (topics, new_off) = get_topics_for_forum(forum, is_moderator, off, MAX_TOPICS)
    tvals = {
      'siteroot' : siteroot,
      'siteurl' : self.request.url,
      'forum' : forum,
      'topics' : topics,
      'forums' : db.GqlQuery("SELECT * FROM Forum where is_disabled = False").fetch(MAX_FORUMS),
      'analytics_code' : forum.analytics_code or "",
      'new_from' : new_off,
      'log_in_out' : get_log_in_out(siteroot)
    }
    tmpl = os.path.join(tmpldir, "topic_list.html")
    self.template_out(tmpl, tvals)

# responds to /<forumurl>/topic?id=<id>
class TopicForm(FofouBase):

  def get(self, *args):
    if not self.personalize_page_and_get_enrolled():
      return
    (forum, siteroot, tmpldir) = forum_siteroot_tmpldir_from_url(self.request.path_info)
    if not forum or forum.is_disabled:
      return self.redirect(FORUMS_ROOT + "/")

    topic_id = self.request.get('id')
    if not topic_id:
      return self.redirect(siteroot)

    topic = db.get(db.Key.from_path('Topic', int(topic_id)))
    if not topic:
      return self.redirect(siteroot)

    is_moderator = users.is_current_user_admin()
    if topic.is_deleted and not is_moderator:
      return self.redirect(siteroot)

    is_archived = False
    # Note: auto-archiving disabled
    #now = datetime.datetime.now()
    #week = datetime.timedelta(days=7)
    #week = datetime.timedelta(seconds=7)
    #if now > topic.created_on + week:
    #  is_archived = True

    # 200 is more than generous
    MAX_POSTS = 200
    if is_moderator:
      posts = Post.gql("WHERE forum = :1 AND topic = :2 ORDER BY created_on", forum, topic).fetch(MAX_POSTS)
    else:
      posts = Post.gql("WHERE forum = :1 AND topic = :2 AND is_deleted = False ORDER BY created_on", forum, topic).fetch(MAX_POSTS)

    if is_moderator:
        for p in posts:
            if 0 != p.user_ip:
              p.user_ip_str = long2ip(p.user_ip)
            if p.user_homepage:
                p.user_homepage = p.user_homepage
    tvals = {
      'siteroot' : siteroot,
      'forum' : forum,
      'forums' : db.GqlQuery("SELECT * FROM Forum where is_disabled = False").fetch(MAX_FORUMS),
      'analytics_code' : forum.analytics_code or "",
      'topic' : topic,
      'is_moderator' : is_moderator,
      'is_archived' : is_archived,
      'posts' : posts,
      'log_in_out' : get_log_in_out(self.request.url),
    }
    tmpl = os.path.join(tmpldir, "topic.html")
    self.template_out(tmpl, tvals)

# responds to /<forumurl>/email[?post_id=<post_id>]
class EmailForm(FofouBase):

  def get(self, *args):
    if not self.personalize_page_and_get_enrolled():
      return
    (forum, siteroot, tmpldir) = forum_siteroot_tmpldir_from_url(self.request.path_info)
    if not forum or forum.is_disabled:
      return self.redirect(FORUMS_ROOT + "/")
    (num1, num2) = (random.randint(1,9), random.randint(1,9))
    post_id = self.request.get("post_id")
    if not post_id: return self.redirect(siteroot)
    post = db.get(db.Key.from_path('Post', int(post_id)))
    if not post: return self.redirect(siteroot)
    to_name = post.user_name or post.user_homepage
    subject = "Re: " + (forum.title or forum.url) + " - " + post.topic.subject
    tvals = {
      'siteroot' : siteroot,
      'forum' : forum,
      'num1' : num1,
      'num2' : num2,
      'num3' : int(num1) + int(num2),
      'post_id' : post_id,
      'to' : to_name,
      'subject' : subject,
      'log_in_out' : get_log_in_out(siteroot + "post")
    }
    tmpl = os.path.join(tmpldir, "email.html")
    self.template_out(tmpl, tvals)

  def post(self):
    if not self.personalize_page_and_get_enrolled():
      return
    (forum, siteroot, tmpldir) = forum_siteroot_tmpldir_from_url(self.request.path_info)
    if not forum or forum.is_disabled:
      return self.redirect(FORUMS_ROOT + "/")
    if self.request.get('Cancel'): self.redirect(siteroot)
    post_id = self.request.get("post_id")
    #logging.info("post_id = %s" % str(post_id))
    if not post_id: return self.redirect(siteroot)
    post = db.get(db.Key.from_path('Post', int(post_id)))
    if not post: return self.redirect(siteroot)
    topic = post.topic
    tvals = {
      'siteroot' : siteroot,
      'forum' : forum,
      'topic' : topic,
      'log_in_out' : get_log_in_out(siteroot + "post")
    }
    tmpl = os.path.join(tmpldir, "email_sent.html")
    self.template_out(tmpl, tvals)

# responds to /<forumurl>/post[?id=<topic_id>]
class PostForm(FofouBase):

  def get(self, *args):
    if not self.personalize_page_and_get_enrolled():
      return
    (forum, siteroot, tmpldir) = forum_siteroot_tmpldir_from_url(self.request.path_info)
    if not forum or forum.is_disabled:
      return self.redirect(FORUMS_ROOT + "/")

    ip = get_remote_ip()
    if ip in BANNED_IPS:
      return fake_error(self.response)

    self.send_cookie()

    rememberChecked = ""
    prevUrl = "http://"
    prevEmail = ""
    prevName = ""
    (num1, num2) = (random.randint(1,9), random.randint(1,9))
    tvals = {
      'siteroot' : siteroot,
      'forum' : forum,
      'forums' : db.GqlQuery("SELECT * FROM Forum where is_disabled = False").fetch(MAX_FORUMS),
      'log_in_out' : get_log_in_out(self.request.url)
    }
    topic_id = self.request.get('id')
    if topic_id:
      topic = db.get(db.Key.from_path('Topic', int(topic_id)))
      if not topic: return self.redirect(siteroot)
      tvals['prevTopicId'] = topic_id
      tvals['prevSubject'] = topic.subject
    tmpl = os.path.join(tmpldir, "post.html")
    self.template_out(tmpl, tvals)

  def post(self, *args):
    if not self.personalize_page_and_get_enrolled():
      return
    (forum, siteroot, tmpldir) = forum_siteroot_tmpldir_from_url(self.request.path_info)
    if not forum or forum.is_disabled:
      return self.redirect(FORUMS_ROOT + "/")
    if self.request.get('Cancel'):
      return self.redirect(siteroot)

    ip = get_remote_ip()
    if ip in BANNED_IPS:
      return self.redirect(siteroot)

    self.send_cookie()

    vals = ['TopicId', 'Subject', 'Message', ]
    (topic_id, subject, message) = req_get_vals(self.request, vals)
    message = to_unicode(message)

    tvals = {
      'siteroot' : siteroot,
      'forums' : db.GqlQuery("SELECT * FROM Forum where is_disabled = False").fetch(MAX_FORUMS),
      'forum' : forum,
      "prevSubject" : subject,
      "prevMessage" : message,
      "log_in_out" : get_log_in_out(siteroot + "post")
    }

    # validate captcha and other values
    errclass = None
    if not message: errclass = "message_class"
    # first post must have subject
    if not topic_id and not subject: errclass = "subject_class"

    # sha.new() doesn't accept Unicode strings, so convert to utf8 first
    message_utf8 = message.encode('UTF-8')
    s = sha.new(message_utf8)
    sha1_digest = s.hexdigest()

    duppost = Post.gql("WHERE sha1_digest = :1", sha1_digest).get()
    if duppost: errclass = "message_class"

    if errclass:
      tvals[errclass] = "error"
      tmpl = os.path.join(tmpldir, "post.html")
      return self.template_out(tmpl, tvals)

    # get user either by google user id or cookie. Create user objects if don't
    # already exist
    existing_user = False
    user_id = users.get_current_user()
    if not user_id:
      self.redirect("/")
      return

    user = Student.get_enrolled_student_by_email(user_id.email())
    if not user:
      self.redirect("/")
      return

    if not topic_id:
      topic = Topic(forum=forum, subject=subject, created_by=user.name)
      topic.put()
    else:
      topic = db.get(db.Key.from_path('Topic', int(topic_id)))
      #assert forum.key() == topic.forum.key()
      topic.ncomments += 1
      topic.put()

    user_ip_str = get_remote_ip()
    user_profile_link = '/wikiprofile?student=%d' % user.wiki_id
    p = Post(topic=topic, forum=forum, user=user, user_ip=0, user_ip_str=user_ip_str, message=message, sha1_digest=sha1_digest, user_name = user.name, user_email = user_id.email(), user_homepage = user_profile_link)
    p.put()
    memcache.delete(rss_memcache_key(forum))
    clear_topics_memcache(forum)
    if topic_id:
      self.redirect(siteroot + "topic?id=" + str(topic_id))
    else:
      self.redirect(siteroot)


from webapp2 import Route
routes = [
        Route('/', ForumList, name="ForumList"),
        Route('/manageforums', ManageForums, name="ManageForums"),
        Route('/<:[^/]+>/postdel', PostDelUndel, name="PostDelUndel"),
        Route('/<:[^/]+>/postundel', PostDelUndel, name="PostDelUndel"),
        Route('/<:[^/]+>/post', PostForm, name="PostForm"),
        Route('/<:[^/]+>/topic', TopicForm, name="TopicForm"),
        #Route('/<:[^/]+>/email', EmailForm, name="EmailForm"),
        Route('/<:[^/]+/?>', TopicList, name="TopicList")]

def main():
  application = webapp.WSGIApplication(routes,
     debug=True)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == "__main__":
  main()

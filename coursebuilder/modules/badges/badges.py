from models import custom_modules
from google.appengine.ext import deferred
from models.models import Student
from models.roles import Roles
from modules.regconf.regconf import FormSubmission
from controllers.utils import BaseHandler
from google.appengine.ext import db
import logging
import unicodecsv as csv
import wtforms as wtf
from markupsafe import Markup
from modules.wikifolios.wiki_models import *
import modules.wikifolios.wikifolios as wf
from modules.wikifolios.page_templates import forms, viewable_model
from collections import defaultdict
import urllib
import re
import itertools
from common import prefetch



module = None

def register_module():
    global module

    handlers = [
            ]
    # def __init__(self, name, desc, global_routes, namespaced_routes):
    module = custom_modules.Module("Badges", "Badges",
            [], handlers)

    return module


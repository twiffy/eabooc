# Copyright 2013 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS-IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Course Builder web application entry point."""

__author__ = 'Pavel Simakov (psimakov@google.com)'

import os

import webapp2

# The following import is needed in order to add third-party libraries.
import appengine_config  # pylint: disable-msg=unused-import

from common import tags
from controllers import sites
from models import custom_modules

# Needs to be before .admin for its ConfigProperty to be registered
import modules.wikifolios.wikifolios
import modules.admin.admin
import modules.announcements.announcements
import modules.booctools.booctools
import modules.courses.courses
import modules.dashboard.dashboard
import modules.oauth2.oauth2
import modules.oeditor.oeditor
import modules.review.review
import modules.csv.student_csv
import modules.regconf.regconf


# use this flag to control debug only features
debug = not appengine_config.PRODUCTION_MODE

# init and enable most known modules
modules.oeditor.oeditor.register_module().enable()
modules.admin.admin.register_module().enable()
modules.dashboard.dashboard.register_module().enable()
modules.announcements.announcements.register_module().enable()
modules.review.review.register_module().enable()
modules.courses.courses.register_module().enable()

# BOOC
modules.wikifolios.wikifolios.register_module().enable()
modules.csv.student_csv.register_module().enable()
modules.regconf.regconf.register_module().enable()
modules.booctools.booctools.register_module().enable()

import modules.badges.badges
modules.badges.badges.register_module().enable()

# register modules that are not enabled by default.
modules.oauth2.oauth2.register_module()

# compute all possible routes
global_routes, namespaced_routes = custom_modules.Registry.get_all_routes()

import modules.forum.main
from webapp2_extras.routes import PathPrefixRoute
global_routes += [
        PathPrefixRoute('/forum', modules.forum.main.routes),
        ]


# routes available at '/%namespace%/' context paths
sites.ApplicationRequestHandler.bind(namespaced_routes)
app_routes = [(r'(.*)', sites.ApplicationRequestHandler)]

# tag extension resource routes
extensions_tag_resource_routes = [(
    '/extensions/tags/.*/resources/.*', tags.ResourcesHandler)]

# i18n configuration for jinja2
webapp2_i18n_config = {'translations_path': os.path.join(
    appengine_config.BUNDLE_ROOT, 'modules/i18n/resources/locale')}

# Enable better jinja2 error backtraces
import sys
if not appengine_config.PRODUCTION_MODE:
    from google.appengine.tools.devappserver2.python import sandbox
    sandbox._WHITE_LIST_C_MODULES += ['_ctypes', 'gestalt']
    #print '\n'.join([str(type(mp)) for mp in sys.meta_path])

# init application
app = webapp2.WSGIApplication(
    global_routes + extensions_tag_resource_routes + app_routes,
    config={'webapp2_extras.i18n': webapp2_i18n_config},
    debug=debug)

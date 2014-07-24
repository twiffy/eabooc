"""
This is just a demo!  In the BOOC, the badges are actually
issued by modules/wikifolios/report_handlers.py!
"""
from google.appengine.ext import db
from common.querymapper import Mapper
import models.models as m_models
from badge_models import Badge
import logging

class BatchBadgeIssuer(Mapper):
    KIND = m_models.Student

    def __init__(self, badge_key, decision_function):
        super(BatchBadgeIssuer, self).__init__()
        self.badge_key = badge_key
        self.should_issue = decision_function
        self.num_checked = 0
        self.num_issued = 0

    def map(self, student):
        self.num_checked += 1
        if self.should_issue(student):
            self.num_issued += 1
            if not Badge.is_issued_to(self.badge_key, student):
                return ([Badge.issue(self.badge_key, student, put=False)], [])
        return ([], [])

    def finish(self):
        logging.info("Out of %d students examined, %d qualified for %s",
                self.num_checked, self.num_issued, db.get(self.badge_key))

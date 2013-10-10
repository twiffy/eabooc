from common.querymapper import Mapper
import models.models as m_models
import logging

class BatchBadgeIssuer(Mapper):
    KIND = m_models.Student

    def __init__(self, badge, decision_function):
        super(BatchBadgeIssuer, self).__init__()
        self.badge = badge
        self.should_issue = decision_function
        self.num_checked = 0
        self.num_issued = 0

    def map(self, student):
        self.num_checked += 1
        if self.should_issue(student):
            self.num_issued += 1
            if not self.badge.is_issued_to(student):
                return ([self.badge.issue(student, put=False)], [])
        return ([], [])

    def finish(self):
        logging.info("Out of %d students examined, %d qualified for %s",
                self.num_checked, self.num_issued, self.badge)

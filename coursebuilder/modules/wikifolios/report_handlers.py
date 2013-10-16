from controllers.utils import BaseHandler
from modules.badges.badge_models import Badge, BadgeAssertion
from report import UnitReport, PartReport
import wtforms as wtf


class EvidenceHandler(BaseHandler):
    def get(self):
        try:
            assertion = BadgeAssertion.get_by_id(int(self.request.GET.get('assertion', -1)))
        except ValueError:
            assertion = None
        if not assertion:
            self.abort(404)

        self.response.write('hi')

        #OK, so maybe something needs to live in the DB that "is" the evidence.
        # It needs to at least give enough info that you can make a PartReport.
        # Can I put something in the badges/ part that is fairly open-ended?


class UnitReportHandler(BaseHandler):
    def get(self):
        try:
            report = UnitReport.get_by_id(int(self.request.GET.get('report', -1)))
        except ValueError:
            report = None
        if not report:
            self.abort(404)

        self.response.write('hi')

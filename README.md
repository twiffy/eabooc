Hello!  Here is an introduction to my modifications to the Google Course
Builder code.  This is based on GCB version 1.4.1, which is tagged V1.4.1 in
the git repository.

Let me begin by acknowleding that the code is pretty tangled and ugly.  At the
time I wrote it, we were under the impression that GCB was going to cease to
exist after version 1.5, so we wouldn't be running any more courses on it.
Thus, re-factoring the code for maintainability was not a big priority.  So, I
feel a bit sheepish.  But really, I think that the lessons learned would be
more significant to you than the code itself anyway, so let's move on.


ASSIGNMENTS
===========

Dan ran this course, using only a Google Sites wiki, for several years before I
showed up.  The "wikifolio" format comes from there.  It's lost almost all
vestiges of wiki-ness: there aren't community-editable spaces, and the students
can't create pages with arbitrary titles.  Anyway, it seemed to work well.  The
majority of the code lives in coursebuilder/modules/wikifolios/ .

Form Fields
-----------

To allow students to input rich text with tables and other useful details, I
chose CKEditor.  For security, we needed to sanitize the HTML.  Bleach seemed
like a good Python library for this.  I wrote some code to make them
interoperate, and to integrate that into the WTForms form library.

	common/ckeditor.py - Convert from Bleach's format for lists of allowed tags, etc., into CKEditor's format.
	modules/wikifolios/wiki_bleach.py - WTForms integration, and my list of allowed tags, styles, etc.  The latter turned out to be a bit finicky.
	views/wf_page.html - in {% if editing %} - the JavaScript for making CKEditor show up.

For the ranking fields, I used JQuery UI's Sortable widget.  To get the
information back into Python land, I used a bit of JavaScript to put the
ranking into a form field, and then some Python code to parse that back out to
a simple ordered list of strings.  I made crosstabulations of these lists to
see which groups preferred which items.

	views/wf_page.html - at the end - JS for the ranking fields.
	modules/wikifolios/ranking.py - WTForms code for rendering the Widget and understanding the contents of the Field.  Django forms probably work differently, I suppose.
	modules/wikifolios/page_templates.py - Example use of the WTForms code.
	common/crosstab.py - a cute class for making cross-tabulations of frequency data, used to show ranking results.
	modules.csv.student_csv.UnitRankingQuery - example use of crosstab on ranking.


BADGES
======

Models and JSON serving
-----------------------

I made a system of badge models and edit/view pages with the least effort
possible.  It worked reasonably well, but there are several awkward points and
known bugs.  Since you're going to use a different library, I'll just point
this out and move on.

	modules/badges/badge_models.py - the badge models!
	modules/badges/badges.py - the request handlers for editing, viewing, and JSON-ing badges.

Student Views of What They Need to Do
-------------------------------------

We decided that we wanted students to be able to see what they needed to
accomplish in order to earn a badge.  When the badge deadline passed, the
status would be frozen, and they would either receive the badge or not.  I
implemented this by creating objects that reported the student's progress.
When the deadline passed, these objects would be saved in the database, but
before that, they were re-calculated each time they were used.  You can see the
front-end of these objects by going to your user's Account page, or by viewing
a badge.

	modules/wikifolios/report.py - the objects representing students' progress.
	A maze of templates starting with views/student_profile.html - the students' view of their badge progress.
	views/wf_evidence_top.html - the template for the front page of a badge.

This model worked, but was really awkward at times.  It might be better to use
a model of student progress that is based on events, and updates when the
student does something.  An additional complication is in the next section...

Deciding Who Gets a Badge
-------------------------

This is surprisingly hard.  It's one of those things, like Payroll, that is
extremely human, even though it seems on the surface to be straightforward and
rule-based.  People ask for extensions, so deadlines are not really a rule.
Rules about what is required to receive a badge may change, or have exceptions.
People may violate academic standards and need to have their badges revoked.
Lots of dimensions where the system needs to be flexible!

These complications are not explicitly modeled in the code for our course.  To
issue badges, I ran a routine that would run all the reports, from the section
above, and serialize them to the database.  Those that met the rules would get
badges issued.  There was also code to force the reports to run again, even
though they were in the database, so that people could get extensions.  If
rules changed, I would change the code and re-run the reports.

This worked OK, but the interaction with the dynamic vs. static report objects
made the issuance routines much more complex than I would have wanted.  Two
independent options were required for each routine.  The routines could either
save the badges & reports to the data store, making them real, or not
("dry-run").  They could also force the reports to be re-run, or not.  And
there were several different types of badges, each of which needed a different
set of rules checked, and needed to support each of these options.

I'm sure there is a better model for all this.  I think that it should support
automatically issuing badges for the common cases, but be flexible enough that
you don't need to change code to make an exception for someone.  Ideally, there
would be a good separation between statistics that are computed and updated,
which won't be fiddled with, and rules about who qualifies, which might be
bent.  The computed statistics could be updated based on events - and hopefully
could be stored in a data store with strong consistency properties.

	modules/wikifolios/report_handlers.py - routines for issuing badges, and for displaying badge evidence to the public.
	common/querymapper.py - App Engine requests must be handled within one minute, so this is the framework for doing small batches of students at a time and avoiding the deadline.


OTHER BITS
==========

Unicode CSV Files
-----------------

Python 2's built-in `csv` module doesn't understand Unicode very well.  It's
much easier to generate Unicode CSV files using the aptly-named unicodecsv
package:

	https://github.com/jdunck/python-unicodecsv

Furthermore, making Excel understand CSV files with Unicode characters in them
is a challenge.  Here is a request handler that creates a CSV file that Excel
understands, and causes it to be downloaded.

	modules.csv.student_csv.TableRenderingHandler - render_as_csv

The "byte order mark" u'\ufeff' shouldn't be required in UTF-8 text, but it
makes Excel notice that the file is Unicode.

Plagiarism Detector
-------------------

It would be easy to work around this, but our students were not very devious.
It detects sequences of words that are shared between student posts.

	modules/csv/plag.py


CONCLUSION
==========

I hope that this has been helpful!  Feel free to write with any questions.

-Thomas Grenfell Smith <thomathom@gmail.com>, April 2014

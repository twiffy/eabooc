import wtforms as wtf
from wtforms.ext.appengine.fields import StringListPropertyField, IntegerListPropertyField
from jinja2 import Markup
from wtforms.widgets.core import html_params, HTMLString, TextArea
from unittest import TestCase

class StringRankingField(StringListPropertyField):
    def __init__(self, label=None, validators=None, choices=None, **kwargs):
        super(StringRankingField, self).__init__(label, validators, **kwargs)
        self.choices = choices

    def pre_validate(self, form):
        if self.data:
            values = set(c[0] for c in self.choices)
            seen = set()
            for d in self.data:
                if d not in values:
                    raise ValueError("'%(value)s' is not a valid choice for this field" % dict(value=d))

                if d in seen:
                    raise ValueError("'%(value)s' is duplicated, but you can only rank it once" % dict(value=d))


class IntegerRankingWidget(object):
    def __call__(self, field, **kwargs):
        class_ = kwargs.get('class', 'integer-ranking')

        html = [Markup('<div class="%s">') % class_]
                
        html.append('<ol %s>' % html_params(**kwargs))
        for index, choice in field.iter_choices():
            html.append(Markup('<li value="%d">%s</li>') % (index, choice))
        html.append('</ol>')
        html.append(TextArea()(field, **kwargs))
        html.append('</div>')
        return u''.join(
                unicode(x) for x in html)


class IntegerRankingField(IntegerListPropertyField):
    widget = IntegerRankingWidget()
    def __init__(self, label=None, validators=None, choices=None, **kwargs):
        kwargs.setdefault('default', choices)
        super(IntegerRankingField, self).__init__(label, validators, **kwargs)
        self.choices = choices

    def _value(self):
        if self.data:
            return '\n'.join([str(self.choices.index(v) + 1) for v in self.data])
        else:
            return '\n'.join([str(i) for i in range(1, len(self.choices) + 1)])

    def iter_choices(self):
        if self.data:
            # TODO: handle ranking e.g. the top 3 of 5 things.
            assert len(self.data) == len(self.choices)
            return [(self.choices.index(v) + 1, v) for v in self.data]
        else:
            return enumerate(self.choices, start=1)

    def process_formdata(self, valuelist):
        # this is broken : it should happen after super() and iterate on .data....
        super(IntegerRankingField, self).process_formdata(valuelist)
        if self.data:
            index_list = self.data
            self.data = []
            try:
                for i in index_list:
                    if i < 1:
                        raise ValueError()
                    self.data.append(self.choices[i - 1])
            except (ValueError, IndexError):
                self.data = None
                raise ValueError('Not a valid item number')


# --------- tests ----------

class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v

class IntegerRankingFieldTest(TestCase):
    class F(wtf.Form):
        a = IntegerRankingField(choices=['cheese', 'ham'])

    def test_with_data(self):
        form = self.F(DummyPostData(a=['1\n2']))
        self.assertEqual(form.a.data, ['cheese', 'ham'])
        self.assertEqual(form.a(), '''<div class="integer-ranking"><ol ><li value="1">cheese</li><li value="2">ham</li></ol><textarea id="a" name="a">1\n2</textarea></div>''')

    def test_re_ordering(self):
        form = self.F(DummyPostData(a='2\n1'))
        self.assertEqual(form.a.data, ['ham', 'cheese'])
        rendered = form.a()
        self.assertLess(rendered.index('ham'), rendered.index('cheese'))

    def test_bad_data(self):
        form = self.F(DummyPostData(a=['3']))
        self.assertEqual(form.a.data, None)

    def test_negative(self):
        form = self.F(DummyPostData(a='-1'))
        self.assertEqual(form.a.data, None)

import wtforms as wtf
from wtforms.ext.appengine.fields import StringListPropertyField, IntegerListPropertyField
from jinja2 import Markup
from wtforms.widgets.core import html_params, HTMLString, TextInput
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
        class_ += ' editable'

        html = [Markup('<div class="%s">') % class_]
                
        html.append('<ol %s>' % html_params(for_=field.id))
        for index, choice in field.iter_choices():
            html.append(Markup('<li value="%d">%s</li>') % (index, choice))
        html.append('</ol>')
        html.append(wtf.widgets.TextInput()(field, **kwargs))
        html.append('</div>')
        return u''.join(
                unicode(x) for x in html)

class ReadOnlyRankingWidget(object):
    def __call__(self, field, **kwargs):
        class_ = kwargs.get('class', 'integer-ranking')

        html = [Markup('<div class="%s">') % class_]

        html.append('<ol>')

        if not field.data:
            html.append(Markup('<li>%s have not been ranked yet.</li>') % (
                ', '.join([choice for i, choice in field.iter_choices()])))
        else:
            for _, choice in field.iter_choices():
                html.append(Markup('<li>%s</li>') % (choice))

        html.append('</ol>')
        html.append('</div>')
        return u''.join(
                unicode(x) for x in html)


class IntegerRankingField(wtf.Field):
    widget = IntegerRankingWidget()
    def __init__(self, label=None, validators=None, choices=None, **kwargs):
        super(IntegerRankingField, self).__init__(label, validators, **kwargs)
        self.choices = choices

    def _value(self):
        if self.data:
            return ', '.join([str(self.choices.index(v) + 1) for v in self.data])
        else:
            return ', '.join([str(i) for i in range(1, len(self.choices) + 1)])

    def iter_choices(self):
        if self.data:
            # TODO: handle ranking e.g. the top 3 of 5 things.
            assert len(self.data) == len(self.choices)
            return [(self.choices.index(v) + 1, v) for v in self.data]
        else:
            return enumerate(self.choices, start=1)

    def parse_int_list(self, raw):
        if raw:
            try:
                return [int(value) for value in raw.split(',')]
            except ValueError:
                raise ValueError('Not a valid list of integers, separated by commas')

    def process_formdata(self, valuelist):
        if valuelist:
            index_list = self.parse_int_list(valuelist[0])
            self.data = []
            try:
                for i in index_list:
                    if i < 1:
                        raise ValueError()
                    self.data.append(self.choices[i - 1])
            except (ValueError, IndexError):
                self.data = None
                raise ValueError('Not a valid item number')

    def read_only_view(self):
        return ReadOnlyRankingWidget()(self)


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
        form = self.F(DummyPostData(a=['1, 2']))
        self.assertEqual(form.a.data, ['cheese', 'ham'])
        rendered = form.a()
        self.assertTrue('integer-ranking' in rendered)
        self.assertTrue('input' in rendered)
        self.assertLess(rendered.index('cheese'), rendered.index('ham'))

    def test_re_ordering(self):
        form = self.F(DummyPostData(a='2,1'))
        self.assertEqual(form.a.data, ['ham', 'cheese'])
        rendered = form.a()
        # since we have the post in opposite order, it must be rendered in opposite order
        self.assertLess(rendered.index('ham'), rendered.index('cheese'))
        # the field value must also be 2,1.
        self.assertLess(rendered.rindex('2'), rendered.rindex('1'))

    def test_bad_data(self):
        form = self.F(DummyPostData(a=['3']))
        self.assertEqual(form.a.data, None)

    def test_negative(self):
        form = self.F(DummyPostData(a='-1'))
        form.validate()
        self.assertEqual(form.a.data, None)
        self.assertGreater(len(form.errors), 0)

    def test_read_only_view(self):
        form = self.F(DummyPostData(a='2, \n\n1'))
        self.assertEqual(form.a.data, ['ham', 'cheese'])
        rend = form.a.read_only_view()
        self.assertLess(rend.index('ham'), rend.index('cheese'))
        self.assertTrue('input' not in rend)
        self.assertTrue('textarea' not in rend)
        self.assertTrue('li' in rend)
        self.assertTrue('not been ranked yet' not in rend)

    def test_no_data_ro_view(self):
        form = self.F(DummyPostData())
        rend = form.a.read_only_view()
        self.assertTrue('input' not in rend)
        self.assertTrue('textarea' not in rend)
        self.assertTrue('ham' in rend)
        self.assertTrue('cheese' in rend)
        self.assertTrue('not been ranked yet' in rend)

    def test_creation_from_model(self):
        class FakeModel(object):
            def __init__(self, **kwargs):
                for k, v in kwargs.iteritems():
                    setattr(self, k, v)
        o = FakeModel(a=['ham', 'cheese'])
        form = self.F(None, o)
        rendered = form.a()
        self.assertLess(rendered.index('ham'), rendered.index('cheese'))
        self.assertLess(rendered.rindex('2'), rendered.rindex('1'))

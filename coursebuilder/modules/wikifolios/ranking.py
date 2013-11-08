import wtforms as wtf
from jinja2 import Markup
from wtforms.widgets.core import html_params, HTMLString, TextInput
from unittest import TestCase


class IntegerRankingWidget(object):
    def __call__(self, field, **kwargs):
        class_ = kwargs.get('class', 'booc-ranking')
        class_ += ' editable'

        html = [Markup('<div class="%s">') % class_]
                
        html.append('<ol %s>' % html_params(for_=field.id))
        for index, choice, label in field.iter_choices_labels():
            html.append(Markup('<li value="%d" rank-value="%d"><strong>%s</strong> %s</li>') % (index, index, choice, label))
        html.append('</ol>')
        html.append(wtf.widgets.TextInput()(field, **kwargs))
        html.append('</div>')
        return u''.join(
                unicode(x) for x in html)

class ReadOnlyIntegerRankingWidget(object):
    def __call__(self, field, **kwargs):
        class_ = kwargs.get('class', 'booc-ranking')

        html = [Markup('<div class="%s">') % class_]

        html.append('<ol>')

        if not field.data:
            html.append(Markup('<li>%s have not been ranked yet.</li>') % (
                ', '.join([choice for i, choice in field.iter_choices()])))
        else:
            for _, choice, label in field.iter_choices_labels():
                html.append(Markup('<li><strong>%s</strong> %s</li>') % (choice, label))

        html.append('</ol>')
        html.append('</div>')
        return u''.join(
                unicode(x) for x in html)


class BaseRankingField(object):
    pass

class StringRankingWidget(object):
    def __call__(self, field, **kwargs):
        class_ = kwargs.get('class', 'booc-ranking')
        class_ += ' editable'

        html = [Markup('<div class="%s">') % class_]
                
        html.append('<ol %s>' % html_params(for_=field.id))
        for choice, label in field.iter_choices():
            html.append(Markup('<li rank-value="%s">%s</li>') % (choice, label))
        html.append('</ol>')
        html.append(wtf.widgets.TextInput()(field, **kwargs))
        html.append('</div>')
        return u''.join(
                unicode(x) for x in html)

class ReadOnlyStringRankingWidget(object):
    def __call__(self, field, **kwargs):
        class_ = kwargs.get('class', 'booc-ranking')

        html = [Markup('<div class="%s">') % class_]

        html.append('<ol>')

        if not field.data:
            html.append('<li>The choices have not been ranked yet.</li>')
        else:
            for _, label in field.iter_choices():
                html.append(Markup('<li>%s</li>') % (label))

        html.append('</ol>')
        html.append('</div>')
        return u''.join(
                unicode(x) for x in html)

class StringRankingField(wtf.Field, BaseRankingField):
    widget = StringRankingWidget()
    def __init__(self, label=None, validators=None, choices=None, **kwargs):
        super(StringRankingField, self).__init__(label, validators, **kwargs)
        self.choices = choices
        self.choice_dict = dict(choices)

    def _value(self):
        "Format the data for the underlying basic input field"
        if self.data:
            return ', '.join(self.data)
        else:
            return ''

    def iter_choices(self):
        if self.data:
            return iter([(item, self.choice_dict[item]) for item in self.data])
        else:
            return iter(self.choices)

    def process_formdata(self, valuelist):
        if not valuelist:
            return

        items = [x.strip() for x in valuelist[0].split(',')]

        # if the set of items differs from the set of choices...
        if len(set(items) ^ self.choice_dict.viewkeys()) != 0:
            raise ValueError('List of responses does not match list of choices')

        self.data = items

    def process_data(self, value):
        self.data = None
        if not value:
            return

        if len(set(value) ^ self.choice_dict.viewkeys()) != 0:
            raise ValueError('List of responses does not match list of choices')
        self.data = value

    def read_only_view(self):
        return ReadOnlyStringRankingWidget()(self)


class IntegerRankingField(wtf.Field, BaseRankingField):
    widget = IntegerRankingWidget()
    def __init__(self, label=None, validators=None, choices=None, labels=None, **kwargs):
        super(IntegerRankingField, self).__init__(label, validators, **kwargs)
        self.labels = labels
        self.choices = choices

    def _value(self):
        "Format the data for the most basic input field - a textinput with a list of comma separated integers"
        if self.data:
            return ', '.join([str(self.choices.index(v) + 1) for v in self.data])
        else:
            return ''

    def iter_choices(self):
        if self.data:
            # TODO: handle ranking e.g. the top 3 of 5 things.
            assert len(self.data) == len(self.choices)
            return [(self.choices.index(v) + 1, v) for v in self.data]
        else:
            return enumerate(self.choices, start=1)

    def iter_choices_labels(self):
        labels = [''] * len(self.choices)
        if self.labels:
            labels = self.labels

        for (idx, choice), label in zip(self.iter_choices(), labels):
            yield (idx, choice, label)

    def parse_int_list(self, raw):
        if raw:
            try:
                return [int(value) for value in raw.split(',')]
            except ValueError:
                raise ValueError('Not a valid list of integers, separated by commas')

    def process_formdata(self, valuelist):
        index_list = None
        if valuelist:
            index_list = self.parse_int_list(valuelist[0])

        if index_list:
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
        return ReadOnlyIntegerRankingWidget()(self)


# --------- tests ----------
class FakeModel(object):
    def __init__(self, **kwargs):
        for k, v in kwargs.iteritems():
            setattr(self, k, v)

class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v

class StringRankingFieldTest(TestCase):
    class F(wtf.Form):
        a = StringRankingField(choices=[
            ('cheese', 'Cheese'), 
            ('ham', 'Ham')])

    def test_create(self):
        form = self.F(DummyPostData(a='ham, cheese'))

    def test_iter_choices(self):
        form = self.F()
        it = form.a.iter_choices()
        self.assertTrue(hasattr(it, 'next'))
        lst = list(it)
        self.assertEqual(form.a.choices, lst)

    def test_process_formdata(self):
        form = self.F(DummyPostData())
        self.assertIsNone(form.a.data)

        form = self.F(DummyPostData(a='ham, cheese'))
        self.assertIsInstance(form.a.data, list)
        self.assertEqual(form.a.data, ['ham', 'cheese'])

    def test_invalid_formdata(self):
        # not enough responses:
        form = self.F(DummyPostData(a='ham'))
        self.assertIsNone(form.a.data)

    def test_wrong_formdata(self):
        # responses are not the right words
        form = self.F(DummyPostData(a='pasta, chili'))
        self.assertIsNone(form.a.data)

    def test_dupes(self):
        # duplicate responses
        form = self.F(DummyPostData(a='ham, ham'))
        self.assertIsNone(form.a.data)

    def test_create_from_model(self):
        model = FakeModel(a=['ham', 'cheese'])
        form = self.F(None, model)
        self.assertEqual(form.a.data, model.a)

    def test_invalid_create_from_model(self):
        model = FakeModel(a=['cheese'])
        form = self.F(None, model)
        self.assertIsNone(form.a.data)

    def test_render(self):
        form = self.F()
        rend = form.a()
        self.assertIn('cheese', rend)
        self.assertIn('Cheese', rend)
        self.assertIn('ham', rend)
        self.assertIn('Ham', rend)

    def test_render_ordered(self):
        form = self.F(DummyPostData(a='ham, cheese'))
        rend = form.a()
        self.assertTrue('rank-value' in rend)
        self.assertLess(rend.index('ham'), rend.index('cheese'))

    def test_render_readonly(self):
        form = self.F(DummyPostData(a='ham, cheese'))
        rend = form.a.read_only_view()


class IntegerRankingFieldTest(TestCase):
    class F(wtf.Form):
        a = IntegerRankingField(choices=['cheese', 'ham'])

    def test_with_data(self):
        form = self.F(DummyPostData(a=['1, 2']))
        self.assertEqual(form.a.data, ['cheese', 'ham'])
        rendered = form.a()
        self.assertTrue('booc-ranking' in rendered)
        self.assertTrue('rank-value' in rendered)
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
        self.assertNotIn('input', rend)
        self.assertNotIn('textarea', rend)
        self.assertIn('li', rend)
        self.assertNotIn('not been ranked yet', rend)

    def test_no_data_view(self):
        form = self.F(DummyPostData())
        rend = form.a()
        self.assertIn('input', rend)
        self.assertIn('ham', rend)
        self.assertIn('cheese', rend)
        self.assertNotIn(',', rend)

    def test_no_data_ro_view(self):
        form = self.F(DummyPostData())
        rend = form.a.read_only_view()
        self.assertNotIn('input', rend)
        self.assertNotIn('textarea', rend)
        self.assertIn('ham', rend)
        self.assertIn('cheese', rend)
        self.assertIn('not been ranked yet', rend)

    def test_creation_from_model(self):
        o = FakeModel(a=['ham', 'cheese'])
        form = self.F(None, o)
        rendered = form.a()
        self.assertLess(rendered.index('ham'), rendered.index('cheese'))
        self.assertLess(rendered.rindex('2'), rendered.rindex('1'))

import wtforms as wtf
from wtforms.ext.appengine.fields import StringListPropertyField

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


if __name__ == '__main__':
    class F(wtf.Form):
        srf = StringRankingField('Awesome', choices=[('a', 'The Letter A'), ('b', 'The Letter B')])

    for fld in F():
        print fld


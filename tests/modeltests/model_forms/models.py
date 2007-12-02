"""
XX. Generating HTML forms from models

This is mostly just a reworking of the form_for_model/form_for_instance tests
to use ModelForm. As such, the text may not make sense in all cases, and the
examples are probably a poor fit for the ModelForm syntax. In other words,
most of these tests should be rewritten.
"""

from django.db import models

ARTICLE_STATUS = (
    (1, 'Draft'),
    (2, 'Pending'),
    (3, 'Live'),
)

class Category(models.Model):
    name = models.CharField(max_length=20)
    slug = models.SlugField(max_length=20)
    url = models.CharField('The URL', max_length=40)

    def __unicode__(self):
        return self.name

class Writer(models.Model):
    name = models.CharField(max_length=50, help_text='Use both first and last names.')

    def __unicode__(self):
        return self.name

class Article(models.Model):
    headline = models.CharField(max_length=50)
    slug = models.SlugField()
    pub_date = models.DateField()
    created = models.DateField(editable=False)
    writer = models.ForeignKey(Writer)
    article = models.TextField()
    categories = models.ManyToManyField(Category, blank=True)
    status = models.IntegerField(choices=ARTICLE_STATUS, blank=True, null=True)

    def save(self):
        import datetime
        if not self.id:
            self.created = datetime.date.today()
        return super(Article, self).save()

    def __unicode__(self):
        return self.headline

class PhoneNumber(models.Model):
    phone = models.PhoneNumberField()
    description = models.CharField(max_length=20)

    def __unicode__(self):
        return self.phone

__test__ = {'API_TESTS': """
>>> from django import newforms as forms
>>> from django.newforms.models import ModelForm

The bare bones, absolutely nothing custom, basic case.

>>> class CategoryForm(ModelForm):
...     class Meta:
...         model = Category
>>> CategoryForm.base_fields.keys()
['name', 'slug', 'url']


Extra fields.

>>> class CategoryForm(ModelForm):
...     some_extra_field = forms.BooleanField()
...
...     class Meta:
...         model = Category

>>> CategoryForm.base_fields.keys()
['name', 'slug', 'url', 'some_extra_field']


Replacing a field.

>>> class CategoryForm(ModelForm):
...     url = forms.BooleanField()
...
...     class Meta:
...         model = Category

>>> CategoryForm.base_fields['url'].__class__
<class 'django.newforms.fields.BooleanField'>


Using 'fields'.

>>> class CategoryForm(ModelForm):
...
...     class Meta:
...         model = Category
...         fields = ['url']

>>> CategoryForm.base_fields.keys()
['url']


Using 'exclude'

>>> class CategoryForm(ModelForm):
...
...     class Meta:
...         model = Category
...         exclude = ['url']

>>> CategoryForm.base_fields.keys()
['name', 'slug']


Using 'fields' *and* 'exclude'. Not sure why you'd want to do this, but uh,
"be liberal in what you accept" and all.

>>> class CategoryForm(ModelForm):
...
...     class Meta:
...         model = Category
...         fields = ['name', 'url']
...         exclude = ['url']

>>> CategoryForm.base_fields.keys()
['name']

Don't allow more than one 'model' definition in the inheritance hierarchy.
Technically, it would generate a valid form, but the fact that the resulting
save method won't deal with multiple objects is likely to trip up people not
familiar with the mechanics.

>>> class CategoryForm(ModelForm):
...     class Meta:
...         model = Category

>>> class BadForm(CategoryForm):
...     class Meta:
...         model = Article
Traceback (most recent call last):
...
ImproperlyConfigured: BadForm defines more than one model.

>>> class ArticleForm(ModelForm):
...     class Meta:
...         model = Article

>>> class BadForm(ArticleForm, CategoryForm):
...     pass
Traceback (most recent call last):
...
ImproperlyConfigured: BadForm's base classes define more than one model.


# Old form_for_x tests #######################################################

>>> from django.newforms import ModelForm, CharField
>>> import datetime

>>> Category.objects.all()
[]

>>> class CategoryForm(ModelForm):
...     class Meta:
...         model = Category
>>> f = CategoryForm(Category())
>>> print f
<tr><th><label for="id_name">Name:</label></th><td><input id="id_name" type="text" name="name" maxlength="20" /></td></tr>
<tr><th><label for="id_slug">Slug:</label></th><td><input id="id_slug" type="text" name="slug" maxlength="20" /></td></tr>
<tr><th><label for="id_url">The URL:</label></th><td><input id="id_url" type="text" name="url" maxlength="40" /></td></tr>
>>> print f.as_ul()
<li><label for="id_name">Name:</label> <input id="id_name" type="text" name="name" maxlength="20" /></li>
<li><label for="id_slug">Slug:</label> <input id="id_slug" type="text" name="slug" maxlength="20" /></li>
<li><label for="id_url">The URL:</label> <input id="id_url" type="text" name="url" maxlength="40" /></li>
>>> print f['name']
<input id="id_name" type="text" name="name" maxlength="20" />

>>> f = CategoryForm(Category(), auto_id=False)
>>> print f.as_ul()
<li>Name: <input type="text" name="name" maxlength="20" /></li>
<li>Slug: <input type="text" name="slug" maxlength="20" /></li>
<li>The URL: <input type="text" name="url" maxlength="40" /></li>

>>> f = CategoryForm(Category(), {'name': 'Entertainment', 'slug': 'entertainment', 'url': 'entertainment'})
>>> f.is_valid()
True
>>> f.cleaned_data
{'url': u'entertainment', 'name': u'Entertainment', 'slug': u'entertainment'}
>>> obj = f.save()
>>> obj
<Category: Entertainment>
>>> Category.objects.all()
[<Category: Entertainment>]

>>> f = CategoryForm(Category(), {'name': "It's a test", 'slug': 'its-test', 'url': 'test'})
>>> f.is_valid()
True
>>> f.cleaned_data
{'url': u'test', 'name': u"It's a test", 'slug': u'its-test'}
>>> obj = f.save()
>>> obj
<Category: It's a test>
>>> Category.objects.order_by('name')
[<Category: Entertainment>, <Category: It's a test>]

If you call save() with commit=False, then it will return an object that
hasn't yet been saved to the database. In this case, it's up to you to call
save() on the resulting model instance.
>>> f = CategoryForm(Category(), {'name': 'Third test', 'slug': 'third-test', 'url': 'third'})
>>> f.is_valid()
True
>>> f.cleaned_data
{'url': u'third', 'name': u'Third test', 'slug': u'third-test'}
>>> obj = f.save(commit=False)
>>> obj
<Category: Third test>
>>> Category.objects.order_by('name')
[<Category: Entertainment>, <Category: It's a test>]
>>> obj.save()
>>> Category.objects.order_by('name')
[<Category: Entertainment>, <Category: It's a test>, <Category: Third test>]

If you call save() with invalid data, you'll get a ValueError.
>>> f = CategoryForm(Category(), {'name': '', 'slug': '', 'url': 'foo'})
>>> f.errors
{'name': [u'This field is required.'], 'slug': [u'This field is required.']}
>>> f.cleaned_data
Traceback (most recent call last):
...
AttributeError: 'CategoryForm' object has no attribute 'cleaned_data'
>>> f.save()
Traceback (most recent call last):
...
ValueError: The Category could not be created because the data didn't validate.
>>> f = CategoryForm(Category(), {'name': '', 'slug': '', 'url': 'foo'})
>>> f.save()
Traceback (most recent call last):
...
ValueError: The Category could not be created because the data didn't validate.

Create a couple of Writers.
>>> w = Writer(name='Mike Royko')
>>> w.save()
>>> w = Writer(name='Bob Woodward')
>>> w.save()

ManyToManyFields are represented by a MultipleChoiceField, ForeignKeys and any
fields with the 'choices' attribute are represented by a ChoiceField.
>>> class ArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = ArticleForm(Article(), auto_id=False)
>>> print f
<tr><th>Headline:</th><td><input type="text" name="headline" maxlength="50" /></td></tr>
<tr><th>Slug:</th><td><input type="text" name="slug" maxlength="50" /></td></tr>
<tr><th>Pub date:</th><td><input type="text" name="pub_date" /></td></tr>
<tr><th>Writer:</th><td><select name="writer">
<option value="" selected="selected">---------</option>
<option value="1">Mike Royko</option>
<option value="2">Bob Woodward</option>
</select></td></tr>
<tr><th>Article:</th><td><textarea rows="10" cols="40" name="article"></textarea></td></tr>
<tr><th>Status:</th><td><select name="status">
<option value="" selected="selected">---------</option>
<option value="1">Draft</option>
<option value="2">Pending</option>
<option value="3">Live</option>
</select></td></tr>
<tr><th>Categories:</th><td><select multiple="multiple" name="categories">
<option value="1">Entertainment</option>
<option value="2">It&#39;s a test</option>
<option value="3">Third test</option>
</select><br /> Hold down "Control", or "Command" on a Mac, to select more than one.</td></tr>

You can restrict a form to a subset of the complete list of fields
by providing a 'fields' argument. If you try to save a
model created with such a form, you need to ensure that the fields
that are _not_ on the form have default values, or are allowed to have
a value of None. If a field isn't specified on a form, the object created
from the form can't provide a value for that field!
>>> class PartialArticleForm(ModelForm):
...     class Meta:
...         model = Article
...         fields = ('headline','pub_date')
>>> f = PartialArticleForm(Article(), auto_id=False)
>>> print f
<tr><th>Headline:</th><td><input type="text" name="headline" maxlength="50" /></td></tr>
<tr><th>Pub date:</th><td><input type="text" name="pub_date" /></td></tr>

Use form_for_instance to create a Form from a model instance. The difference
between this Form and one created via form_for_model is that the object's
current values are inserted as 'initial' data in each Field.
>>> w = Writer.objects.get(name='Mike Royko')
>>> class RoykoForm(ModelForm):
...     class Meta:
...         model = Writer
>>> f = RoykoForm(w, auto_id=False)
>>> print f
<tr><th>Name:</th><td><input type="text" name="name" value="Mike Royko" maxlength="50" /><br />Use both first and last names.</td></tr>

>>> art = Article(headline='Test article', slug='test-article', pub_date=datetime.date(1988, 1, 4), writer=w, article='Hello.')
>>> art.save()
>>> art.id
1
>>> class TestArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = TestArticleForm(art, auto_id=False)
>>> print f.as_ul()
<li>Headline: <input type="text" name="headline" value="Test article" maxlength="50" /></li>
<li>Slug: <input type="text" name="slug" value="test-article" maxlength="50" /></li>
<li>Pub date: <input type="text" name="pub_date" value="1988-01-04" /></li>
<li>Writer: <select name="writer">
<option value="">---------</option>
<option value="1" selected="selected">Mike Royko</option>
<option value="2">Bob Woodward</option>
</select></li>
<li>Article: <textarea rows="10" cols="40" name="article">Hello.</textarea></li>
<li>Status: <select name="status">
<option value="" selected="selected">---------</option>
<option value="1">Draft</option>
<option value="2">Pending</option>
<option value="3">Live</option>
</select></li>
<li>Categories: <select multiple="multiple" name="categories">
<option value="1">Entertainment</option>
<option value="2">It&#39;s a test</option>
<option value="3">Third test</option>
</select>  Hold down "Control", or "Command" on a Mac, to select more than one.</li>
>>> f = TestArticleForm(art, {'headline': u'Test headline', 'slug': 'test-headline', 'pub_date': u'1984-02-06', 'writer': u'1', 'article': 'Hello.'})
>>> f.is_valid()
True
>>> test_art = f.save()
>>> test_art.id
1
>>> test_art = Article.objects.get(id=1)
>>> test_art.headline
u'Test headline'

You can create a form over a subset of the available fields
by specifying a 'fields' argument to form_for_instance.
>>> class PartialArticleForm(ModelForm):
...     class Meta:
...         model = Article
...         fields=('headline', 'slug', 'pub_date')
>>> f = PartialArticleForm(art, {'headline': u'New headline', 'slug': 'new-headline', 'pub_date': u'1988-01-04'}, auto_id=False)
>>> print f.as_ul()
<li>Headline: <input type="text" name="headline" value="New headline" maxlength="50" /></li>
<li>Slug: <input type="text" name="slug" value="new-headline" maxlength="50" /></li>
<li>Pub date: <input type="text" name="pub_date" value="1988-01-04" /></li>
>>> f.is_valid()
True
>>> new_art = f.save()
>>> new_art.id
1
>>> new_art = Article.objects.get(id=1)
>>> new_art.headline
u'New headline'

Add some categories and test the many-to-many form output.
>>> new_art.categories.all()
[]
>>> new_art.categories.add(Category.objects.get(name='Entertainment'))
>>> new_art.categories.all()
[<Category: Entertainment>]
>>> class TestArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = TestArticleForm(new_art, auto_id=False)
>>> print f.as_ul()
<li>Headline: <input type="text" name="headline" value="New headline" maxlength="50" /></li>
<li>Slug: <input type="text" name="slug" value="new-headline" maxlength="50" /></li>
<li>Pub date: <input type="text" name="pub_date" value="1988-01-04" /></li>
<li>Writer: <select name="writer">
<option value="">---------</option>
<option value="1" selected="selected">Mike Royko</option>
<option value="2">Bob Woodward</option>
</select></li>
<li>Article: <textarea rows="10" cols="40" name="article">Hello.</textarea></li>
<li>Status: <select name="status">
<option value="" selected="selected">---------</option>
<option value="1">Draft</option>
<option value="2">Pending</option>
<option value="3">Live</option>
</select></li>
<li>Categories: <select multiple="multiple" name="categories">
<option value="1" selected="selected">Entertainment</option>
<option value="2">It&#39;s a test</option>
<option value="3">Third test</option>
</select>  Hold down "Control", or "Command" on a Mac, to select more than one.</li>

>>> f = TestArticleForm(new_art, {'headline': u'New headline', 'slug': u'new-headline', 'pub_date': u'1988-01-04',
...     'writer': u'1', 'article': u'Hello.', 'categories': [u'1', u'2']})
>>> new_art = f.save()
>>> new_art.id
1
>>> new_art = Article.objects.get(id=1)
>>> new_art.categories.order_by('name')
[<Category: Entertainment>, <Category: It's a test>]

Now, submit form data with no categories. This deletes the existing categories.
>>> f = TestArticleForm(new_art, {'headline': u'New headline', 'slug': u'new-headline', 'pub_date': u'1988-01-04',
...     'writer': u'1', 'article': u'Hello.'})
>>> new_art = f.save()
>>> new_art.id
1
>>> new_art = Article.objects.get(id=1)
>>> new_art.categories.all()
[]

Create a new article, with categories, via the form.
>>> class ArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = ArticleForm(Article(), {'headline': u'The walrus was Paul', 'slug': u'walrus-was-paul', 'pub_date': u'1967-11-01',
...     'writer': u'1', 'article': u'Test.', 'categories': [u'1', u'2']})
>>> new_art = f.save()
>>> new_art.id
2
>>> new_art = Article.objects.get(id=2)
>>> new_art.categories.order_by('name')
[<Category: Entertainment>, <Category: It's a test>]

Create a new article, with no categories, via the form.
>>> class ArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = ArticleForm(Article(), {'headline': u'The walrus was Paul', 'slug': u'walrus-was-paul', 'pub_date': u'1967-11-01',
...     'writer': u'1', 'article': u'Test.'})
>>> new_art = f.save()
>>> new_art.id
3
>>> new_art = Article.objects.get(id=3)
>>> new_art.categories.all()
[]

Create a new article, with categories, via the form, but use commit=False.
The m2m data won't be saved until save_m2m() is invoked on the form.
>>> class ArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = ArticleForm(Article(), {'headline': u'The walrus was Paul', 'slug': 'walrus-was-paul', 'pub_date': u'1967-11-01',
...     'writer': u'1', 'article': u'Test.', 'categories': [u'1', u'2']})
>>> new_art = f.save(commit=False)

# Manually save the instance
>>> new_art.save()
>>> new_art.id
4

# The instance doesn't have m2m data yet
>>> new_art = Article.objects.get(id=4)
>>> new_art.categories.all()
[]

# Save the m2m data on the form
>>> f.save_m2m()
>>> new_art.categories.order_by('name')
[<Category: Entertainment>, <Category: It's a test>]

Here, we define a custom ModelForm. Because it happens to have the same fields as
the Category model, we can just call the form's save() to apply its changes to an
existing Category instance.
>>> class ShortCategory(ModelForm):
...     name = CharField(max_length=5)
...     slug = CharField(max_length=5)
...     url = CharField(max_length=3)
>>> cat = Category.objects.get(name='Third test')
>>> cat
<Category: Third test>
>>> cat.id
3
>>> form = ShortCategory(cat, {'name': 'Third', 'slug': 'third', 'url': '3rd'})
>>> form.save()
<Category: Third>
>>> Category.objects.get(id=3)
<Category: Third>

Here, we demonstrate that choices for a ForeignKey ChoiceField are determined
at runtime, based on the data in the database when the form is displayed, not
the data in the database when the form is instantiated.
>>> class ArticleForm(ModelForm):
...     class Meta:
...         model = Article
>>> f = ArticleForm(Article(), auto_id=False)
>>> print f.as_ul()
<li>Headline: <input type="text" name="headline" maxlength="50" /></li>
<li>Slug: <input type="text" name="slug" maxlength="50" /></li>
<li>Pub date: <input type="text" name="pub_date" /></li>
<li>Writer: <select name="writer">
<option value="" selected="selected">---------</option>
<option value="1">Mike Royko</option>
<option value="2">Bob Woodward</option>
</select></li>
<li>Article: <textarea rows="10" cols="40" name="article"></textarea></li>
<li>Status: <select name="status">
<option value="" selected="selected">---------</option>
<option value="1">Draft</option>
<option value="2">Pending</option>
<option value="3">Live</option>
</select></li>
<li>Categories: <select multiple="multiple" name="categories">
<option value="1">Entertainment</option>
<option value="2">It&#39;s a test</option>
<option value="3">Third</option>
</select>  Hold down "Control", or "Command" on a Mac, to select more than one.</li>
>>> Category.objects.create(name='Fourth', url='4th')
<Category: Fourth>
>>> Writer.objects.create(name='Carl Bernstein')
<Writer: Carl Bernstein>
>>> print f.as_ul()
<li>Headline: <input type="text" name="headline" maxlength="50" /></li>
<li>Slug: <input type="text" name="slug" maxlength="50" /></li>
<li>Pub date: <input type="text" name="pub_date" /></li>
<li>Writer: <select name="writer">
<option value="" selected="selected">---------</option>
<option value="1">Mike Royko</option>
<option value="2">Bob Woodward</option>
<option value="3">Carl Bernstein</option>
</select></li>
<li>Article: <textarea rows="10" cols="40" name="article"></textarea></li>
<li>Status: <select name="status">
<option value="" selected="selected">---------</option>
<option value="1">Draft</option>
<option value="2">Pending</option>
<option value="3">Live</option>
</select></li>
<li>Categories: <select multiple="multiple" name="categories">
<option value="1">Entertainment</option>
<option value="2">It&#39;s a test</option>
<option value="3">Third</option>
<option value="4">Fourth</option>
</select>  Hold down "Control", or "Command" on a Mac, to select more than one.</li>

# ModelChoiceField ############################################################

>>> from django.newforms import ModelChoiceField, ModelMultipleChoiceField

>>> f = ModelChoiceField(Category.objects.all())
>>> list(f.choices)
[(u'', u'---------'), (1, u'Entertainment'), (2, u"It's a test"), (3, u'Third'), (4, u'Fourth')]
>>> f.clean('')
Traceback (most recent call last):
...
ValidationError: [u'This field is required.']
>>> f.clean(None)
Traceback (most recent call last):
...
ValidationError: [u'This field is required.']
>>> f.clean(0)
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. That choice is not one of the available choices.']
>>> f.clean(3)
<Category: Third>
>>> f.clean(2)
<Category: It's a test>

# Add a Category object *after* the ModelChoiceField has already been
# instantiated. This proves clean() checks the database during clean() rather
# than caching it at time of instantiation.
>>> Category.objects.create(name='Fifth', url='5th')
<Category: Fifth>
>>> f.clean(5)
<Category: Fifth>

# Delete a Category object *after* the ModelChoiceField has already been
# instantiated. This proves clean() checks the database during clean() rather
# than caching it at time of instantiation.
>>> Category.objects.get(url='5th').delete()
>>> f.clean(5)
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. That choice is not one of the available choices.']

>>> f = ModelChoiceField(Category.objects.filter(pk=1), required=False)
>>> print f.clean('')
None
>>> f.clean('')
>>> f.clean('1')
<Category: Entertainment>
>>> f.clean('100')
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. That choice is not one of the available choices.']

# queryset can be changed after the field is created.
>>> f.queryset = Category.objects.exclude(name='Fourth')
>>> list(f.choices)
[(u'', u'---------'), (1, u'Entertainment'), (2, u"It's a test"), (3, u'Third')]
>>> f.clean(3)
<Category: Third>
>>> f.clean(4)
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. That choice is not one of the available choices.']


# ModelMultipleChoiceField ####################################################

>>> f = ModelMultipleChoiceField(Category.objects.all())
>>> list(f.choices)
[(1, u'Entertainment'), (2, u"It's a test"), (3, u'Third'), (4, u'Fourth')]
>>> f.clean(None)
Traceback (most recent call last):
...
ValidationError: [u'This field is required.']
>>> f.clean([])
Traceback (most recent call last):
...
ValidationError: [u'This field is required.']
>>> f.clean([1])
[<Category: Entertainment>]
>>> f.clean([2])
[<Category: It's a test>]
>>> f.clean(['1'])
[<Category: Entertainment>]
>>> f.clean(['1', '2'])
[<Category: Entertainment>, <Category: It's a test>]
>>> f.clean([1, '2'])
[<Category: Entertainment>, <Category: It's a test>]
>>> f.clean((1, '2'))
[<Category: Entertainment>, <Category: It's a test>]
>>> f.clean(['100'])
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. 100 is not one of the available choices.']
>>> f.clean('hello')
Traceback (most recent call last):
...
ValidationError: [u'Enter a list of values.']

# Add a Category object *after* the ModelMultipleChoiceField has already been
# instantiated. This proves clean() checks the database during clean() rather
# than caching it at time of instantiation.
>>> Category.objects.create(id=6, name='Sixth', url='6th')
<Category: Sixth>
>>> f.clean([6])
[<Category: Sixth>]

# Delete a Category object *after* the ModelMultipleChoiceField has already been
# instantiated. This proves clean() checks the database during clean() rather
# than caching it at time of instantiation.
>>> Category.objects.get(url='6th').delete()
>>> f.clean([6])
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. 6 is not one of the available choices.']

>>> f = ModelMultipleChoiceField(Category.objects.all(), required=False)
>>> f.clean([])
[]
>>> f.clean(())
[]
>>> f.clean(['10'])
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. 10 is not one of the available choices.']
>>> f.clean(['3', '10'])
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. 10 is not one of the available choices.']
>>> f.clean(['1', '10'])
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. 10 is not one of the available choices.']

# queryset can be changed after the field is created.
>>> f.queryset = Category.objects.exclude(name='Fourth')
>>> list(f.choices)
[(1, u'Entertainment'), (2, u"It's a test"), (3, u'Third')]
>>> f.clean([3])
[<Category: Third>]
>>> f.clean([4])
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. 4 is not one of the available choices.']
>>> f.clean(['3', '4'])
Traceback (most recent call last):
...
ValidationError: [u'Select a valid choice. 4 is not one of the available choices.']


# PhoneNumberField ############################################################

>>> class PhoneNumberForm(ModelForm):
...     class Meta:
...         model = PhoneNumber
>>> f = PhoneNumberForm(PhoneNumber(), {'phone': '(312) 555-1212', 'description': 'Assistance'})
>>> f.is_valid()
True
>>> f.cleaned_data
{'phone': u'312-555-1212', 'description': u'Assistance'}
"""}

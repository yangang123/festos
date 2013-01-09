# Create your views here.
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.utils.datastructures import SortedDict 
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from haystack.views import basic_search, SearchView
from haystack.query import SearchQuerySet
from haystack.forms import SearchForm
from books.models import Book
from books.forms import BookForm, EditBookForm, SearchBookForm



class SearchBookView(SearchView):
    def get_results(self):
        """
        Fetches the results via the form.

        Returns an empty list if there's no query to search with.
        """

        results = self.form.search()

        # if there is no 'q' haystack returns an empty results
        #import ipdb; ipdb.set_trace()
        if results.count() == 0 and \
                len(self.request.GET) > 0 and not \
                self.request.GET.has_key('q'):
            results = SearchQuerySet()

        url_query = ""
        self.vs_query = ""

        books = Book.objects.all()
        if self.request.user.is_authenticated():
            books = books.filter(Q(owner_id = self.request.user.id) | 
                                 Q(public = True))
        else:
            books = books.filter(public = True)


        if (self.request.GET.has_key('q')):
            self.vs_query += " text:" + self.request.GET.get('q')


        form=SearchBookForm(self.request.GET)        
        if form.is_valid():
            opts = {}
            for key in form.cleaned_data:
                if form.cleaned_data[key] != '':
                    opts[key+'__icontains'] = form.cleaned_data[key]
                    self.vs_query += " " + key + ":" + form.cleaned_data[key]
            books = books.filter(**opts)


        results = results.filter(document_id__in = \
            books.values_list('id', flat=True))

        return results

    def extra_context(self):
        """
        Allows the addition of more context variables as needed.

        Must return a dictionary.
        """

        documents = SortedDict()
        for r in self.results:
            if r.document_id in documents:
                documents[r.document_id]['pages'].append(r.object)
            else:
                documents[r.document_id]={'id': r.object.document.id,
                                          'document': r.object.document,
                                          'notes': r.notes,
                                          'source': r.source,
                                          'description': r.description,
                                          'pages': [r.object] }


        paginator =  Paginator(documents.items(), 5)
        try:
            page = self.request.GET.get('pag')
            docs = paginator.page(page)
        except PageNotAnInteger:
            # If page is not an integer, deliver first page.
            docs = paginator.page(1)
        except EmptyPage:
            # If page is out of range (e.g. 9999), 
            # deliver last page of   results.
            docs = paginator.page(paginator.num_pages)

        cp = self.request.GET.copy()
        if cp.has_key('pag'):
            cp.pop('pag')

        return {'docs': docs,
                'total': len(documents),
                'vs_query': self.vs_query,
                'url_query': cp.urlencode }

#def search_books(search_book_view):
#  return search_book_view;

search_book = SearchBookView(form_class=SearchForm)

@login_required
def list_books(request):
    """ Add a book """

    books = Book.objects.filter(owner=request.user)

    return render_to_response('list_books.html', {
                                'books': books,
                                }, context_instance=RequestContext(request))


@login_required
def add_book(request):
    """ Add a book """
    form = BookForm(user=request.user)
    if request.method == 'POST':
        form = BookForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            form.save()
            file = form.cleaned_data['file']
            form.instance.set_file(file = file, filename=file.name)
            return HttpResponseRedirect(reverse('books.views.list_books'))

    return render_to_response('add_book.html', {
                                'form': form,
                                }, context_instance=RequestContext(request))

@login_required
def edit_book(request, pk):
    """ Edit a book """
    book = Book.objects.get(pk=pk)
    form = EditBookForm(instance = book)
    if request.method == 'POST':
        form = EditBookForm(request.POST, instance = book)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse('books.views.list_books'))

    return render_to_response('edit_book.html', {
                                'book': book,
                                'form': form,
                                }, context_instance=RequestContext(request))
                                
@login_required
def remove_book(request, pk):
    """ Remove a book """

    book = Book.objects.get(pk=pk)
    book.delete()
    return HttpResponseRedirect(reverse('books.views.list_books'))

@login_required
def change_privacy_book(request, pk):
    """ Remove a book """

    book = Book.objects.get(pk=pk)
    book.public = not book.public
    book.save()
    return HttpResponseRedirect(reverse('books.views.list_books'))

from django.contrib import admin
from django import forms

from .models import Item, Category, Author

from import_export import resources, fields, widgets
from import_export.admin import ImportExportModelAdmin



from mptt.admin import DraggableMPTTAdmin, TreeRelatedFieldListFilter, MPTTModelAdmin

import random

from import_export.results import RowResult


# Resource Classes

class CategoryResource(resources.ModelResource):

    parent = fields.Field(
        column_name='parent',
        attribute='parent',
        widget = widgets.ForeignKeyWidget(Category, 'title'))

    class Meta: 
        model = Category
        skip_unchanged = True
        report_skipped = True
        exclude = ('id',)
        import_id_fields = ('title',)
        
class SkipErrorRessource(resources.ModelResource):
    
    report_error_column=False  # a parameter to report table column not defined in the resource class
    
    def get_field_column_names(self):
        names = []
        for field in self.get_fields():
            names.append(field.column_name)  # >> get the field name 'used' name
        return names

    def import_row(self, row, instance_loader, **kwargs):
        import_result = super(SkipErrorRessource, self).import_row(
            row, instance_loader, **kwargs
        )

        if import_result.import_type == RowResult.IMPORT_TYPE_ERROR:
            import_result.diff=[]
            for field in self.get_fields():    # >> loop throught the field directly and gather from the field column name instead of field name
                import_result.diff.append(row.get(field.column_name, ''))
            
            if self.report_error_column:  # >> to report eventual columnds not in the resources definition, to help spotting the issue.
                for row_name in row:
                    if not row_name in self.get_field_column_names():
                        import_result.diff.append(row.get(row_name, ''))

            # Add a column with the error message
            import_result.diff.append(
                "Errors: {}".format(
                    [err.error for err in import_result.errors]
                )
                )
            # clear errors and mark the record to skip
            import_result.errors = []
            import_result.import_type = RowResult.IMPORT_TYPE_SKIP

        return import_result

    class Meta:
        abstract = True
        model = Item          
        
        
   
        
    

# Admin Classes

@admin.register(Author)

class AuthorAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("author_name",)}
    list_display = ['author_name', 'id']    
    search_fields = ['author_name']
    ordering = ('-author_name',)
    save_on_top = True
    list_per_page = 50
    fields = (("author_name", "slug","author_image",),     
  
    "author_posts",
    "description",

    
    )

@admin.register(Item)

class ItemAdmin(ImportExportModelAdmin, admin.ModelAdmin):
    resource_class = SkipErrorRessource
    prepopulated_fields = {"slug": ("title",)}
    list_display = ['title', 'is_published', 'id']
    list_filter = ('category', )
    search_fields = ['title', 'metatitle', 'metadescription']
    ordering = ('-id',)
    save_on_top = True
    list_per_page = 50
    fields = ("is_published",("title", "slug","category",),     
    ("image",),
    'author', 'views',
    "description", "shortdescription", 
    "metatitle", "metadescription",  
	
    "plitka_top", 

    
    )
    


@admin.register(Category)

class CategoryAdmin(ImportExportModelAdmin, MPTTModelAdmin):
    resource_class = CategoryResource
    
    prepopulated_fields = {"slug": ("title",)}
    list_display = ("title", "menutitle", "id", "slug")
    ordering = ('-id',)
    search_fields = ['title','id','slug']
    list_per_page = 500
    save_on_top = True
    mptt_level_indent = 30
    mptt_indent_field = "title"
    list_filter =(('parent', TreeRelatedFieldListFilter),)
    
    fields = (("title","parent", "slug", "menutitle",),
        "description", "metatitle", "metadescription",
        "plitka_top", "plitka_bottom", "plitka_search",
        )
    
    

    
    

admin.site.site_title = "DomoProektor.ru"
admin.site.site_header = "DomoProektor.ru"

from typing import Any, Dict
from django.core.mail import send_mail
from django.db import models
from django.db.models.query import QuerySet
from django.dispatch import receiver
from django.shortcuts import render,redirect, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models.signals import post_save
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponse
from django.views.generic import TemplateView,ListView,DetailView,CreateView,UpdateView,DeleteView,FormView
from .models import Lead,Agent,User,UserProfile,Category
from .form import LeadForm,LeadModelForm,CustomUserSignupForm,AssignAgentForm
from agents.mixins import OrganisorAndLoginRequiredMixin

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from .tokens import account_activation_token
from django.core.mail import EmailMessage
from django.contrib import messages


def verify_email(request):
    if request.method == "POST":
        if request.user.email_is_verified != True:
            current_site = get_current_site(request)
            user = request.user
            email = request.user.email
            subject = "Verify Email"
            message = render_to_string('user/verify_email_message.html', {
                'request': request,
                'user': user,
                'domain': current_site.domain,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':account_activation_token.make_token(user),
            })
            email = EmailMessage(
                subject, message, to=[email]
            )
            email.content_subtype = 'html'
            email.send()
            return redirect('verify-email-done')
        else:
            return redirect('signup')
    return render(request, 'user/verify_email.html')

def verify_email_done(request):
    return render(request, 'users/verify_email_done.html')


# Create your views here.
class Signup(CreateView):
    template_name = 'registration/signup.html' 
    form_class = CustomUserSignupForm

    def get_success_url(self):
        return reverse('login')

class LandingPageView( TemplateView):
    template_name = 'landing.html'

def landing(request):
    return render(request,'landing.html')

class LeadListView(LoginRequiredMixin,ListView):
    template_name = 'leads\leads_list.html'
    context_object_name = 'leads'

    def get_queryset(self):
        user = self.request.user

        if user.is_organisor:
            queryset = Lead.objects.filter(organisation = user.userprofile, agent__isnull = False)
        if user.is_agent:
            queryset = Lead.objects.filter(organisation = user.agent.organisation, agent__isnull = False)
            queryset = queryset.filter(agent__user = user)
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super(LeadListView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation = user.userprofile,agent__isnull = True)
            context.update({
            'unassigned_leads': queryset
            })
        return context

def lead_list(request):
    leads = Lead.objects.all()
    context = {"leads":leads}
    return render(request, 'leads\leads_list.html',context)

class LeadDetailView(LoginRequiredMixin,DetailView):
    template_name = 'leads\leads_details.html'
    context_object_name = "lead"
    
    def get_queryset(self):
        user = self.request.user

        if user.is_organisor:
            queryset = Lead.objects.filter(organisation = user.userprofile)
        if user.is_agent:
            queryset = Lead.objects.filter(organisation = user.agent.organisation)
            queryset = queryset.filter(agent__user = user)
        return queryset

def lead_details(request,pk):
    lead = Lead.objects.get(id=pk)
    context = {'lead':lead}
    return render(request, 'leads\leads_details.html',context)

class LeadCreateView(OrganisorAndLoginRequiredMixin,CreateView):
    template_name = 'leads/lead_create.html' 
    form_class = LeadModelForm

    def get_success_url(self):
        return reverse('leads:lead-list')
    
    def form_valid(self,form):
        lead = form.save(commit=False)
        lead.organisation = self.request.user.userprofile
        lead.save()

        send_mail(
            subject='A new Lead has been created',
            message="Visit the website to view the Lead",
            from_email='test@test.com',
            recipient_list=['test2@test.com']
        )
        return super(LeadCreateView,self).form_valid(form)
         
# def lead_create(request):
    # form =LeadModelForm()
    # if(request.method == 'POST'):
    #     form = LeadModelForm(request.POST)
    #     if(form.is_valid()):
    #         print(form.cleaned_data)
    #         new_lead = form.save(commit=False)
    #         new_lead.first_name = form.cleaned_data["first_name"]
    #         new_lead.last_name = form.cleaned_data["last_name"]
    #         new_lead.age = form.cleaned_data["age"]
    #         new_lead.agent = form.cleaned_data["agent"]
    #         new_lead.organisation = request.user.userprofile
    #         new_lead.save()

    #         # Lead.objects.create(
    #         #     first_name = new_lead.first_name,
    #         #     last_name =new_lead.last_name,
    #         #     age= new_lead.age,
    #         #     agent=new_lead.agent,
    #         #     organisation = new_lead.organisation
    #         # )
    #         return redirect('/leads')
    # context = {
    #     'form':form
    # }
    # return render(request,'leads/lead_create.html',context)

class LeadUpdateView(OrganisorAndLoginRequiredMixin,UpdateView):
    template_name = 'leads\lead_update.html'
    form_class = LeadModelForm

    def get_success_url(self):
        return reverse('leads:lead-list')
    
    def get_queryset(self):
        user = self.request.user
        return Lead.objects.filter(organisation = user.userprofile)
        

def lead_update(request,pk):
    lead = Lead.objects.get(id = pk)
    form = LeadModelForm(instance=lead)
    if(request.method == "POST"):
        form = LeadModelForm(request.POST,instance=lead)
        if(form.is_valid()):
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            age = form.cleaned_data['age']
            lead.first_name = first_name
            lead.last_name = last_name
            lead.age =age
            lead.save()
            return redirect('/leads')
    context = {
        "form" : form,
        "lead" : lead
    }
    return render(request,'leads\lead_update.html',context)

class LeadDeleteView(OrganisorAndLoginRequiredMixin,DeleteView):
    template_name = 'leads\lead_delete.html'

    def get_success_url(self):
        return reverse('leads:lead-list')
    
    def get_queryset(self):
        user = self.request.user
        return Lead.objects.filter(organisation = user.userprofile)



def lead_delete(request,pk):
    lead = Lead.objects.get(id = pk)
    lead.delete()
    return redirect('/leads')

@receiver(post_save, sender=User)

def post_user_created(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user = instance)
        print(instance)

class AssignAgentView(OrganisorAndLoginRequiredMixin, FormView):
    template_name = "leads/assign_agent.html"
    form_class = AssignAgentForm

    def get_form_kwargs(self, **kwargs):
        kwargs = super(AssignAgentView, self).get_form_kwargs(**kwargs)
        kwargs.update({
            "request": self.request
        })
        return kwargs
        
    def get_success_url(self):
        return reverse("leads:lead-list")

    def form_valid(self, form):
        agent = form.cleaned_data["agent"]
        lead = Lead.objects.get(id=self.kwargs["pk"])
        lead.agent = agent
        lead.save()
        return super(AssignAgentView, self).form_valid(form)

class CategoryListView(LoginRequiredMixin, ListView):
    template_name = 'leads/category_list.html'
    context_object_name = 'category_list'

    def get_context_data(self, **kwargs):
        context = super(CategoryListView, self).get_context_data(**kwargs)
        user = self.request.user
        if user.is_organisor:
            queryset = Lead.objects.filter(organisation = user.userprofile)
        if user.is_agent:
            queryset = Lead.objects.filter(organisation = user.agent.organisation)
        
        context.update({
            'unassigned_lead_count': queryset.filter(category__isnull = True).count()
        })
        return context
    
    def get_queryset(self):
        user = self.request.user

        if user.is_organisor:
            queryset = Category.objects.filter(organisation = user.userprofile)
        if user.is_agent:
            queryset = Category.objects.filter(organisation = user.agent.organisation)
        return queryset

class CategoryDetailView(LoginRequiredMixin,DetailView):
    template_name = 'leads\category_details.html'
    context_object_name = "category"
    
    # def get_context_data(self, **kwargs):
    #     context = super(CategoryDetailView, self).get_context_data(**kwargs)
    #     # leads = Lead.objects.filter(category = self.get_object())
    #     category_name = self.kwargs.get('category_name', '').lower()

    #     # Filter the Lead objects based on the category name
    #     leads = Lead.objects.filter(category__name=category_name)
    #     context.update({
    #         "leads": leads
    #     })
        # return context
    
    def get_queryset(self):
        user = self.request.user

        if user.is_organisor:
            queryset = Lead.objects.filter(organisation = user.userprofile)
        if user.is_agent:
            queryset = Lead.objects.filter(organisation = user.agent.organisation)
            queryset = queryset.filter(agent__user = user)
        return queryset

class CategoryUpdateView(LoginRequiredMixin,UpdateView):
    template_name = 'leads\category_update.html'
    form_class = LeadModelForm

    def get_success_url(self):
        return reverse('leads:lead-list')
    
    def get_queryset(self):
        user = self.request.user
        return Lead.objects.filter(organistation = user.userprofile)    

# def lead_update(request,pk):
#     lead = Lead.objects.get(id = pk)
#     form = LeadForm()
#     if(request.method == "POST"):
#         form = LeadForm(request.POST)
#         if(form.is_valid()):
#             first_name = form.cleaned_data['first_name']
#             last_name = form.cleaned_data['last_name']
#             age = form.cleaned_data['age']
#             lead.first_name = first_name
#             lead.last_name = last_name
#             lead.age =age
#             lead.save()
#             return redirect('/leads')
#     context = {
#         "form" : form,
#         "lead" : lead
#     }
#     return render(request,'leads\lead_update.html',context)

# def lead_create(request):
#     form =LeadForm()
#     if(request.method == 'POST'):
#         form = LeadForm(request.POST)
#         if(form.is_valid()):
#             print(form.cleaned_data)
#             first_name = form.cleaned_data["first_name"]
#             last_name = form.cleaned_data["last_name"]
#             age = form.cleaned_data["age"]
#             agent = Agent.objects.first()
#             Lead.objects.create(
#                 first_name = first_name,
#                 last_name =last_name,
#                 age= age,
#                 agent=agent
#             )
#             return redirect('/leads')
#     context = {
#         'form':form
#     }
#     return render(request,'leads/lead_create.html',context)
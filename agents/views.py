from typing import Any
import random
from django.db import models
from django.db.models.query import QuerySet
from django.forms.models import BaseModelForm
from django.http import HttpResponse
from django.shortcuts import render,reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView,CreateView,DetailView,DeleteView,UpdateView
from leads.models import Agent, UserProfile
from .form import AgentModelForm
from .mixins import OrganisorAndLoginRequiredMixin
from django.core.mail import send_mail


# Create your views here.

class AgentsListView(OrganisorAndLoginRequiredMixin,ListView):
    template_name = 'agents/agent_list.html'
    context_object_name = 'agents'

    def get_queryset(self):
        organisation = self.request.user.userprofile
        return Agent.objects.filter(organisation = organisation)

class AgentCreateView(OrganisorAndLoginRequiredMixin,CreateView):
    template_name = 'agents/agent_create.html'
    form_class = AgentModelForm

    def get_success_url(self):
        return reverse('agents:agent-list')
    
    def form_valid(self,form):
        user = form.save(commit=False)
        user.is_agent = True
        user.is_organisor = False
        user.set_password(f"{random.randint(1,1000000)}")
        user.save()
        Agent.objects.create(
            user = user,
            organisation = self.request.user.userprofile
        )
        send_mail(
            subject='You are invited to be an agent',
            message='You were requested  to login to start working as an agent on Django CRM',
            from_email='admin@test.com',
            recipient_list=[user.email]
        )
        return super(AgentCreateView,self).form_valid(form)

class AgentDetailView(OrganisorAndLoginRequiredMixin,DetailView):
    template_name = 'agents/agent_details.html'
    content_object_name = 'agents'

    def get_queryset(self):
        organisation = self.request.user.userprofile
        return Agent.objects.filter(organisation = organisation)

class AgentUpdateView(OrganisorAndLoginRequiredMixin, UpdateView):
    template_name = 'agents/agent_update.html'
    form_class = AgentModelForm
    

    def get_success_url(self):
        return reverse('agents:agent-list')
    
    def get_queryset(self):
        organisation = self.request.user.userprofile
        return Agent.objects.filter(organisation = organisation)
    

class AgentDeleteView(LoginRequiredMixin,DeleteView):
    template_name = 'agents/agent_delete.html'

    def get_success_url(self):
        return reverse('agents:agent-list')
    
    def get_queryset(self):
        organisation = self.request.user.userprofile
        return Agent.objects.filter(organisation = organisation)
    


    

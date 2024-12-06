import trace
import traceback
from .constants import *
from django.shortcuts import get_object_or_404
from .models import Issue, Project, User
from .serializers import IssueSerializer, UserSerializer, ProjectSerializer, IssueRequestValidator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.contrib.auth import authenticate

class CustomePagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'limit'
    max_page_size = 200

    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'page_size': self.page_size,
            'results': data
        })


class UserRegister(APIView):
    def post(self, request):
        try:
            user = UserSerializer(data=request.data)
            if user.is_valid():
                user.save()
                return Response(user.data, status=status.HTTP_200_OK)
            
            return Response({'data': [], 'errors': user.errors}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({'errors': {'internal_error': ['Something went wrong']}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLogin(APIView):
    def post(self, request):
        try:
            if 'email' not in request.data or 'password' not in request.data:
                return Response({'errors': {'authentication_error': ['Email/password is required']}}, status=status.HTTP_200_OK)

            email = request.data['email']
            password = request.data['password']

            user = authenticate(request, email=email, password=password)

            if user:
                token = RefreshToken.for_user(user)
                return Response({
                    'message': 'logged in succesfully',
                    'refresh_token': str(token),
                    'access_token': str(token.access_token)
                }, status=status.HTTP_200_OK)
            
            return Response({'errors': {'authentication_error': ['email or password is invalid']}}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            print(e)
            return Response({'errors': {'internal_error': ['Something went wrong']}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserLogout(APIView):
    def post(self, request):
        try:
            refresh_token = request.data['refresh_token']
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
            
            return Response({'message': 'Refresh token is required'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            print(e)
            return Response({'errors': {'internal_error': ['Something went wrong']}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ProjectView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
            Get all project
        """
        try:
            projects = Project.objects.order_by('-updated_at')

            custom_limit = request.GET.get('page_size') 
            search_string = request.GET.get('search', None)

            if search_string:
                projects = projects.filter(title__contains=search_string)

            paginator = CustomePagination()

            paginated_projects = paginator.paginate_queryset(projects, request)
            serialized_projects = ProjectSerializer(paginated_projects, many=True)

            return paginator.get_paginated_response(serialized_projects.data)
        except Exception as e:
            print(e)
            traceback.print_exc()
            return Response({'internal_error': ['Something went wrong']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        """
            Create project
        """
        try:
            serialized_project = ProjectSerializer(data=request.data)
            if serialized_project.is_valid():
                serialized_project.save(owner=User.objects.first())
                return Response(serialized_project.data, status=status.HTTP_200_OK)
            
            return Response(serialized_project.errors, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            print(e)
            traceback.print_exc()
            return Response({'internal_error': ['Something went wrong']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)    


class ProjectDetailView(APIView):
    # permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            project = get_object_or_404(Project, owner=request.user, pk=pk)
            serialized_project = ProjectSerializer(project)
            return Response({'data': serialized_project.data}, status=status.HTTP_200_OK)
        except Project.DoesNotExist:
            return Response({'message': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            return Response({'internal_error': ['Something went wrong']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        """
            update project
        """
        try:
            project = get_object_or_404(Project, pk=pk)
            # project = get_object_or_404(Project, owner=request.user, pk=pk)
            if project:
                serialized_project = ProjectSerializer(project, data=request.data)

                if serialized_project.is_valid():
                    serialized_project.save()
                    return Response(serialized_project.data, status=status.HTTP_200_OK)

                return Response({'data': [], 'errors': serialized_project.errors}, status=status.HTTP_400_BAD_REQUEST)     
        except Project.DoesNotExist:
            return Response({'data': [], 'message': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            return Response({'errors': {'internal_error': ['Something went wrong']}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        """
            delete project
        """
        try:
            project = get_object_or_404(Project, pk=pk)
            # project = get_object_or_404(Project, owner=request.user, pk=pk)
            if project:
                project.delete()
                return Response({'message': 'Project removed'}, status=status.HTTP_200_OK)            
        except Project.DoesNotExist:
            return Response({'data': [], 'message': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            print(e)
            traceback.print_exc()
            return Response({'errors': {'internal_error': ['Something went wrong']}}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class IssueView(APIView):
    def get(self, request):
        try:
            # TODO:: add the owner filter here
            issues = Issue.objects.all()
            serialized_issues = IssueSerializer(issues, many=True)

            request_data = IssueRequestValidator(data=request.data)

            sort_key = 'updated_at',
            sort_value = 'desc'
            if request_data.is_valid():
                sort_key = request_data.validated_data.get('sort_key', 'updated_at')
                sort_value = request_data.validated_data.get('sort_value', 'desc')

                title = request_data.validated_data.get('title', None)
                description = request_data.validated_data.get('description', None)

                if title:
                    issues = issues.filter(title__in=title)
                
                if description:
                    issues = issues.filter(description__in=description)

            order_by = f"-{sort_key}" if sort_value == DESCENDING_ORDER else f"{sort_key}"

            issues = issues.order_by(order_by)

            paginator = CustomePagination()
            paginated_issues = paginator.paginate_queryset(issues, request)
            serialized_issues = IssueSerializer(paginated_issues, many=True)

            return paginator.get_paginated_response(serialized_issues.data)
        except Exception as e:
            print(e)
            return Response({'internal_error': ['Something went wrong']}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

"""
Framework Signature Detection Engine for the Technology Extraction System.

This module provides functionality for detecting framework-specific signatures
and patterns in source code to identify technologies being used.
"""
import json
import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Union

from tech_extraction.config import settings
from tech_extraction.models.framework import (
    FrameworkSignature,
    PatternMatch,
    PatternType,
    SignatureCategory,
)
from tech_extraction.models.file import FileInfo

logger = logging.getLogger(__name__)


class SignatureDetectionEngine:
    """
    Engine for detecting technology signatures in source code files.
    
    The SignatureDetectionEngine performs the following operations:
    1. Load framework signature patterns from registry
    2. Detect framework-specific patterns in source code
    3. Score and categorize pattern matches
    """
    
    def __init__(self, pattern_registry_path: Optional[Path] = None):
        """
        Initialize the signature detection engine.
        
        Args:
            pattern_registry_path: Path to the pattern registry directory
        """
        self.pattern_registry_path = pattern_registry_path or settings.framework_detection.pattern_registry_path
        self.signatures: Dict[str, List[FrameworkSignature]] = {}
        self.matches: Dict[str, List[PatternMatch]] = {}  # Framework -> matches
        
        # Initialize with builtin patterns
        self._load_builtin_patterns()
        
        # Load patterns from registry if available
        if self.pattern_registry_path and Path(self.pattern_registry_path).exists():
            self._load_patterns_from_registry()
    
    def _load_builtin_patterns(self):
        """Load built-in framework signature patterns."""
        # JavaScript/TypeScript frameworks
        self._add_signature_group("react", [
            FrameworkSignature(
                name="React JSX syntax",
                pattern=r"<([A-Z][a-zA-Z0-9]*|>)",
                file_patterns=["*.jsx", "*.tsx", "*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.SYNTAX,
                is_definitive=False,
                weight=0.5,
                example="<Component prop={value} />",
            ),
            FrameworkSignature(
                name="React component definition",
                pattern=r"class\s+[A-Z][a-zA-Z0-9]*\s+extends\s+(?:React\.)?Component",
                file_patterns=["*.jsx", "*.tsx", "*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.CLASS_DEFINITION,
                is_definitive=True,
                weight=1.0,
                example="class MyComponent extends React.Component {",
            ),
            FrameworkSignature(
                name="React functional component",
                pattern=r"(?:const|let|var)\s+[A-Z][a-zA-Z0-9]*\s+=\s+(?:\([^)]*\)|[a-zA-Z0-9_]+)\s+=>\s*(?:<|\{|function)",
                file_patterns=["*.jsx", "*.tsx", "*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_DEFINITION,
                is_definitive=False,
                weight=0.8,
                example="const MyComponent = () => <div>Hello</div>",
            ),
            FrameworkSignature(
                name="React hooks",
                pattern=r"use[A-Z][a-zA-Z0-9]*\s*\(",
                file_patterns=["*.jsx", "*.tsx", "*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="const [state, setState] = useState(initialState);",
            ),
            FrameworkSignature(
                name="React.createElement",
                pattern=r"React\.createElement\s*\(",
                file_patterns=["*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="React.createElement('div', null, 'Hello');",
            ),
        ])
        
        self._add_signature_group("angular", [
            FrameworkSignature(
                name="Angular Component decorator",
                pattern=r"@Component\s*\(\s*\{",
                file_patterns=["*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.DECORATOR,
                is_definitive=True,
                weight=1.0,
                example="@Component({ selector: 'app-root', templateUrl: './app.component.html' })",
            ),
            FrameworkSignature(
                name="Angular Module decorator",
                pattern=r"@NgModule\s*\(\s*\{",
                file_patterns=["*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.DECORATOR,
                is_definitive=True,
                weight=1.0,
                example="@NgModule({ declarations: [AppComponent], imports: [BrowserModule] })",
            ),
            FrameworkSignature(
                name="Angular Injectable decorator",
                pattern=r"@Injectable\s*\(\s*\{",
                file_patterns=["*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.DECORATOR,
                is_definitive=True,
                weight=1.0,
                example="@Injectable({ providedIn: 'root' })",
            ),
            FrameworkSignature(
                name="Angular template binding",
                pattern=r"\[\([a-zA-Z0-9]+\)\]|[(]click[)]|\[\w+\]|{{.*?}}",
                file_patterns=["*.html", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.TEMPLATE,
                is_definitive=True,
                weight=0.9,
                example="<div [property]=\"value\" (click)=\"handler()\" [(ngModel)]=\"property\">{{value}}</div>",
            ),
        ])
        
        self._add_signature_group("vue", [
            FrameworkSignature(
                name="Vue component definition",
                pattern=r"Vue\.component\s*\(\s*['\"][^'\"]+['\"]\s*,\s*\{",
                file_patterns=["*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="Vue.component('my-component', { template: '<div>{{msg}}</div>', data() { return { msg: 'Hello' } } })",
            ),
            FrameworkSignature(
                name="Vue instance",
                pattern=r"new\s+Vue\s*\(\s*\{",
                file_patterns=["*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.INSTANTIATION,
                is_definitive=True,
                weight=1.0,
                example="new Vue({ el: '#app', data: { message: 'Hello Vue!' } })",
            ),
            FrameworkSignature(
                name="Vue single-file component",
                pattern=r"<template>[\s\S]*?<\/template>",
                file_patterns=["*.vue"],
                type=PatternType.REGEX,
                category=SignatureCategory.FILE_FORMAT,
                is_definitive=True,
                weight=1.0,
                example="<template><div>Hello</div></template>",
            ),
            FrameworkSignature(
                name="Vue directives",
                pattern=r"v-(?:if|else|for|show|bind|on|model)",
                file_patterns=["*.vue", "*.html", "*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.DIRECTIVE,
                is_definitive=True,
                weight=1.0,
                example="<div v-if=\"show\">Conditionally rendered</div>",
            ),
        ])
        
        # Python frameworks
        self._add_signature_group("django", [
            FrameworkSignature(
                name="Django model definition",
                pattern=r"class\s+\w+\s*\(\s*(?:models\.)?Model\s*\)",
                file_patterns=["*.py"],
                type=PatternType.REGEX,
                category=SignatureCategory.CLASS_DEFINITION,
                is_definitive=True,
                weight=1.0,
                example="class Post(models.Model):",
            ),
            FrameworkSignature(
                name="Django view definition",
                pattern=r"class\s+\w+\s*\(\s*(?:generic\.)?(?:View|ListView|DetailView|CreateView|UpdateView|DeleteView|TemplateView)\s*\)",
                file_patterns=["*.py"],
                type=PatternType.REGEX,
                category=SignatureCategory.CLASS_DEFINITION,
                is_definitive=True,
                weight=1.0,
                example="class PostListView(generic.ListView):",
            ),
            FrameworkSignature(
                name="Django URL patterns",
                pattern=r"(?:url|path|re_path)\s*\(\s*['\"][^'\"]*['\"]",
                file_patterns=["*.py"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="path('blog/<int:pk>/', views.PostDetail.as_view(), name='post_detail')",
            ),
            FrameworkSignature(
                name="Django template tags",
                pattern=r"{%\s*(?:if|for|block|extends|include|load|url|csrf_token)",
                file_patterns=["*.html", "*.txt", "*.py"],
                type=PatternType.REGEX,
                category=SignatureCategory.TEMPLATE,
                is_definitive=True,
                weight=1.0,
                example="{% if user.is_authenticated %}Hello, {{ user.username }}!{% endif %}",
            ),
        ])
        
        self._add_signature_group("flask", [
            FrameworkSignature(
                name="Flask application instance",
                pattern=r"(?:app|application)\s*=\s*Flask\s*\(",
                file_patterns=["*.py"],
                type=PatternType.REGEX,
                category=SignatureCategory.INSTANTIATION,
                is_definitive=True,
                weight=1.0,
                example="app = Flask(__name__)",
            ),
            FrameworkSignature(
                name="Flask route decorator",
                pattern=r"@(?:\w+\.)?route\s*\(\s*['\"][^'\"]*['\"]",
                file_patterns=["*.py"],
                type=PatternType.REGEX,
                category=SignatureCategory.DECORATOR,
                is_definitive=True,
                weight=1.0,
                example="@app.route('/home')",
            ),
            FrameworkSignature(
                name="Flask template rendering",
                pattern=r"render_template\s*\(\s*['\"][^'\"]*['\"]",
                file_patterns=["*.py"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="return render_template('index.html', title='Home')",
            ),
        ])
        
        self._add_signature_group("fastapi", [
            FrameworkSignature(
                name="FastAPI application instance",
                pattern=r"(?:app|application)\s*=\s*FastAPI\s*\(",
                file_patterns=["*.py"],
                type=PatternType.REGEX,
                category=SignatureCategory.INSTANTIATION,
                is_definitive=True,
                weight=1.0,
                example="app = FastAPI()",
            ),
            FrameworkSignature(
                name="FastAPI route decorator",
                pattern=r"@(?:\w+\.)?(?:get|post|put|delete|patch|options|head)\s*\(\s*['\"][^'\"]*['\"]",
                file_patterns=["*.py"],
                type=PatternType.REGEX,
                category=SignatureCategory.DECORATOR,
                is_definitive=True,
                weight=1.0,
                example="@app.get('/items/{item_id}')",
            ),
            FrameworkSignature(
                name="Pydantic model inheritance",
                pattern=r"class\s+\w+\s*\(\s*BaseModel\s*\)",
                file_patterns=["*.py"],
                type=PatternType.REGEX,
                category=SignatureCategory.CLASS_DEFINITION,
                is_definitive=False,
                weight=0.7,
                example="class Item(BaseModel):",
            ),
        ])
        
        # Java frameworks
        self._add_signature_group("spring", [
            FrameworkSignature(
                name="Spring Boot application",
                pattern=r"@SpringBootApplication",
                file_patterns=["*.java", "*.kt"],
                type=PatternType.REGEX,
                category=SignatureCategory.DECORATOR,
                is_definitive=True,
                weight=1.0,
                example="@SpringBootApplication\npublic class Application {",
            ),
            FrameworkSignature(
                name="Spring REST controller",
                pattern=r"@RestController",
                file_patterns=["*.java", "*.kt"],
                type=PatternType.REGEX,
                category=SignatureCategory.DECORATOR,
                is_definitive=True,
                weight=1.0,
                example="@RestController\npublic class UserController {",
            ),
            FrameworkSignature(
                name="Spring MVC controller",
                pattern=r"@Controller",
                file_patterns=["*.java", "*.kt"],
                type=PatternType.REGEX,
                category=SignatureCategory.DECORATOR,
                is_definitive=True,
                weight=1.0,
                example="@Controller\npublic class HomeController {",
            ),
            FrameworkSignature(
                name="Spring request mapping",
                pattern=r"@(?:Request|Get|Post|Put|Delete|Patch)Mapping",
                file_patterns=["*.java", "*.kt"],
                type=PatternType.REGEX,
                category=SignatureCategory.DECORATOR,
                is_definitive=True,
                weight=1.0,
                example="@GetMapping('/users')\npublic List<User> getAllUsers() {",
            ),
            FrameworkSignature(
                name="Spring component/service/repository",
                pattern=r"@(?:Component|Service|Repository)",
                file_patterns=["*.java", "*.kt"],
                type=PatternType.REGEX,
                category=SignatureCategory.DECORATOR,
                is_definitive=True,
                weight=1.0,
                example="@Service\npublic class UserService {",
            ),
        ])
        
        # PHP frameworks
        self._add_signature_group("laravel", [
            FrameworkSignature(
                name="Laravel controller definition",
                pattern=r"class\s+\w+Controller\s+extends\s+(?:Base)?Controller",
                file_patterns=["*.php"],
                type=PatternType.REGEX,
                category=SignatureCategory.CLASS_DEFINITION,
                is_definitive=True,
                weight=1.0,
                example="class UserController extends Controller",
            ),
            FrameworkSignature(
                name="Laravel model definition",
                pattern=r"class\s+\w+\s+extends\s+Model",
                file_patterns=["*.php"],
                type=PatternType.REGEX,
                category=SignatureCategory.CLASS_DEFINITION,
                is_definitive=True,
                weight=1.0,
                example="class User extends Model",
            ),
            FrameworkSignature(
                name="Laravel facade usage",
                pattern=r"(?:Auth|DB|Cache|Config|Event|Log|Mail|Queue|Route|Session|Storage|URL|Validator)::",
                file_patterns=["*.php"],
                type=PatternType.REGEX,
                category=SignatureCategory.STATIC_CALL,
                is_definitive=True,
                weight=1.0,
                example="DB::table('users')->get()",
            ),
            FrameworkSignature(
                name="Laravel routes",
                pattern=r"Route::(?:get|post|put|patch|delete|options|any)",
                file_patterns=["*.php"],
                type=PatternType.REGEX,
                category=SignatureCategory.STATIC_CALL,
                is_definitive=True,
                weight=1.0,
                example="Route::get('/users', [UserController::class, 'index'])",
            ),
            FrameworkSignature(
                name="Laravel blade templates",
                pattern=r"@(?:if|foreach|for|while|section|yield|include|extends)",
                file_patterns=["*.blade.php"],
                type=PatternType.REGEX,
                category=SignatureCategory.TEMPLATE,
                is_definitive=True,
                weight=1.0,
                example="@foreach($users as $user)\n  {{ $user->name }}\n@endforeach",
            ),
        ])
        
        # Node.js frameworks
        self._add_signature_group("express", [
            FrameworkSignature(
                name="Express application instance",
                pattern=r"(?:const|let|var)\s+(?:\w+)\s*=\s*express\(\)",
                file_patterns=["*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.INSTANTIATION,
                is_definitive=True,
                weight=1.0,
                example="const app = express()",
            ),
            FrameworkSignature(
                name="Express middleware usage",
                pattern=r"app\.use\s*\(",
                file_patterns=["*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=False,
                weight=0.7,
                example="app.use(express.json())",
            ),
            FrameworkSignature(
                name="Express route definition",
                pattern=r"app\.(get|post|put|delete|patch)\s*\(\s*['\"][^'\"]*['\"]",
                file_patterns=["*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="app.get('/users', (req, res) => {})",
            ),
            FrameworkSignature(
                name="Express router",
                pattern=r"(?:const|let|var)\s+(?:\w+)\s*=\s*express\.Router\(\)",
                file_patterns=["*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.INSTANTIATION,
                is_definitive=True,
                weight=1.0,
                example="const router = express.Router()",
            ),
        ])
        
        self._add_signature_group("next.js", [
            FrameworkSignature(
                name="Next.js page component",
                pattern=r"export\s+default\s+function\s+\w+\s*\(",
                file_patterns=["*/pages/*.js", "*/pages/*.tsx", "*/src/pages/*.js", "*/src/pages/*.tsx"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_DEFINITION,
                is_definitive=False,
                weight=0.5,
                example="export default function Home() {",
            ),
            FrameworkSignature(
                name="Next.js getServerSideProps",
                pattern=r"export\s+(?:const|async function|function)\s+getServerSideProps",
                file_patterns=["*.js", "*.tsx"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_DEFINITION,
                is_definitive=True,
                weight=1.0,
                example="export async function getServerSideProps(context) {",
            ),
            FrameworkSignature(
                name="Next.js getStaticProps",
                pattern=r"export\s+(?:const|async function|function)\s+getStaticProps",
                file_patterns=["*.js", "*.tsx"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_DEFINITION,
                is_definitive=True,
                weight=1.0,
                example="export async function getStaticProps(context) {",
            ),
            FrameworkSignature(
                name="Next.js getStaticPaths",
                pattern=r"export\s+(?:const|async function|function)\s+getStaticPaths",
                file_patterns=["*.js", "*.tsx"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_DEFINITION,
                is_definitive=True,
                weight=1.0,
                example="export async function getStaticPaths() {",
            ),
            FrameworkSignature(
                name="Next.js Link component",
                pattern=r"<Link\s+href=",
                file_patterns=["*.js", "*.tsx"],
                type=PatternType.REGEX,
                category=SignatureCategory.COMPONENT_USAGE,
                is_definitive=True,
                weight=0.9,
                example="<Link href='/about'>About</Link>",
            ),
        ])
        
        # Ruby frameworks
        self._add_signature_group("rails", [
            FrameworkSignature(
                name="Rails controller definition",
                pattern=r"class\s+\w+Controller\s*<\s*(?:ApplicationController|ActionController::Base)",
                file_patterns=["*.rb"],
                type=PatternType.REGEX,
                category=SignatureCategory.CLASS_DEFINITION,
                is_definitive=True,
                weight=1.0,
                example="class UsersController < ApplicationController",
            ),
            FrameworkSignature(
                name="Rails model definition",
                pattern=r"class\s+\w+\s*<\s*(?:ApplicationRecord|ActiveRecord::Base)",
                file_patterns=["*.rb"],
                type=PatternType.REGEX,
                category=SignatureCategory.CLASS_DEFINITION,
                is_definitive=True,
                weight=1.0,
                example="class User < ApplicationRecord",
            ),
            FrameworkSignature(
                name="Rails migration",
                pattern=r"class\s+\w+\s*<\s*ActiveRecord::Migration",
                file_patterns=["*.rb"],
                type=PatternType.REGEX,
                category=SignatureCategory.CLASS_DEFINITION,
                is_definitive=True,
                weight=1.0,
                example="class CreateUsers < ActiveRecord::Migration[6.1]",
            ),
            FrameworkSignature(
                name="Rails routes",
                pattern=r"(?:get|post|put|patch|delete)\s+['\"][^'\"]*['\"]",
                file_patterns=["routes.rb"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="get '/users', to: 'users#index'",
            ),
            FrameworkSignature(
                name="Rails view helpers",
                pattern=r"<%=\s*(?:link_to|form_for|form_with|render|content_for|image_tag)",
                file_patterns=["*.erb", "*.html.erb"],
                type=PatternType.REGEX,
                category=SignatureCategory.TEMPLATE,
                is_definitive=True,
                weight=1.0,
                example="<%= link_to 'Home', root_path %>",
            ),
        ])
        
        # Database ORM frameworks
        self._add_signature_group("sqlalchemy", [
            FrameworkSignature(
                name="SQLAlchemy model definition",
                pattern=r"class\s+\w+\s*\(\s*(?:Base|db\.Model)\s*\)",
                file_patterns=["*.py"],
                type=PatternType.REGEX,
                category=SignatureCategory.CLASS_DEFINITION,
                is_definitive=True,
                weight=1.0,
                example="class User(Base):",
            ),
            FrameworkSignature(
                name="SQLAlchemy column definition",
                pattern=r"(?:Column|db\.Column)\s*\(",
                file_patterns=["*.py"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="username = Column(String(50), unique=True)",
            ),
            FrameworkSignature(
                name="SQLAlchemy relationship",
                pattern=r"(?:relationship|db\.relationship)\s*\(",
                file_patterns=["*.py"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="posts = relationship('Post', back_populates='author')",
            ),
            FrameworkSignature(
                name="SQLAlchemy session usage",
                pattern=r"(?:session|db\.session)\.(?:query|add|delete|commit)",
                file_patterns=["*.py"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="users = session.query(User).all()",
            ),
        ])
        
        self._add_signature_group("mongoose", [
            FrameworkSignature(
                name="Mongoose schema definition",
                pattern=r"(?:const|let|var)\s+\w+Schema\s*=\s*new\s+(?:mongoose\.)?Schema\s*\(",
                file_patterns=["*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.INSTANTIATION,
                is_definitive=True,
                weight=1.0,
                example="const userSchema = new Schema({",
            ),
            FrameworkSignature(
                name="Mongoose model creation",
                pattern=r"(?:mongoose\.)?model\s*\(\s*['\"][^'\"]*['\"]",
                file_patterns=["*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="const User = mongoose.model('User', userSchema)",
            ),
            FrameworkSignature(
                name="Mongoose query methods",
                pattern=r"\.(?:find|findOne|findById|create|updateOne|deleteOne)\s*\(",
                file_patterns=["*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=False,
                weight=0.7,
                example="User.find({ active: true })",
            ),
        ])
        
        # Front-end frameworks and libraries
        self._add_signature_group("redux", [
            FrameworkSignature(
                name="Redux createStore",
                pattern=r"(?:const|let|var)\s+\w+\s*=\s*createStore\s*\(",
                file_patterns=["*.js", "*.ts", "*.jsx", "*.tsx"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="const store = createStore(rootReducer)",
            ),
            FrameworkSignature(
                name="Redux action types",
                pattern=r"(?:const|let|var)\s+\w+_(?:REQUEST|SUCCESS|FAILURE|LOADING|LOADED|ERROR)\s*=",
                file_patterns=["*.js", "*.ts", "*.jsx", "*.tsx"],
                type=PatternType.REGEX,
                category=SignatureCategory.VARIABLE_DEFINITION,
                is_definitive=False,
                weight=0.6,
                example="const FETCH_USERS_REQUEST = 'FETCH_USERS_REQUEST'",
            ),
            FrameworkSignature(
                name="Redux reducer function",
                pattern=r"function\s+\w+Reducer\s*\(\s*(?:state\s*=\s*initialState|state|action)",
                file_patterns=["*.js", "*.ts", "*.jsx", "*.tsx"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_DEFINITION,
                is_definitive=True,
                weight=1.0,
                example="function userReducer(state = initialState, action) {",
            ),
            FrameworkSignature(
                name="Redux combineReducers",
                pattern=r"combineReducers\s*\(\s*\{",
                file_patterns=["*.js", "*.ts", "*.jsx", "*.tsx"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="const rootReducer = combineReducers({",
            ),
            FrameworkSignature(
                name="Redux connect",
                pattern=r"connect\s*\(\s*(?:mapStateToProps|mapDispatchToProps|\(|null)",
                file_patterns=["*.js", "*.ts", "*.jsx", "*.tsx"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="export default connect(mapStateToProps)(UserList)",
            ),
            FrameworkSignature(
                name="Redux Toolkit createSlice",
                pattern=r"createSlice\s*\(\s*\{",
                file_patterns=["*.js", "*.ts", "*.jsx", "*.tsx"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="const userSlice = createSlice({",
            ),
        ])
        
        self._add_signature_group("graphql", [
            FrameworkSignature(
                name="GraphQL schema definition",
                pattern=r"(?:const|let|var)\s+\w+\s*=\s*(?:gql|graphql)`\s*(?:type|input|interface|enum|union|schema)",
                file_patterns=["*.js", "*.ts", "*.jsx", "*.tsx", "*.graphql", "*.gql"],
                type=PatternType.REGEX,
                category=SignatureCategory.SCHEMA,
                is_definitive=True,
                weight=1.0,
                example="const typeDefs = gql`\n  type User {\n    id: ID!\n    name: String\n  }\n`",
            ),
            FrameworkSignature(
                name="GraphQL query/mutation",
                pattern=r"(?:query|mutation)\s+\w+\s*(?:\(|{)",
                file_patterns=["*.js", "*.ts", "*.jsx", "*.tsx", "*.graphql", "*.gql"],
                type=PatternType.REGEX,
                category=SignatureCategory.QUERY,
                is_definitive=True,
                weight=1.0,
                example="query GetUsers {\n  users {\n    id\n    name\n  }\n}",
            ),
            FrameworkSignature(
                name="GraphQL resolver",
                pattern=r"const\s+resolvers\s*=\s*{",
                file_patterns=["*.js", "*.ts"],
                type=PatternType.REGEX,
                category=SignatureCategory.OBJECT_DEFINITION,
                is_definitive=True,
                weight=1.0,
                example="const resolvers = {\n  Query: {\n    users: () => users\n  }\n}",
            ),
            FrameworkSignature(
                name="Apollo Client",
                pattern=r"(?:new\s+ApolloClient|ApolloClient\s*\(\s*\{)",
                file_patterns=["*.js", "*.ts", "*.jsx", "*.tsx"],
                type=PatternType.REGEX,
                category=SignatureCategory.INSTANTIATION,
                is_definitive=True,
                weight=1.0,
                example="const client = new ApolloClient({",
            ),
            FrameworkSignature(
                name="Apollo useQuery hook",
                pattern=r"useQuery\s*\(\s*(?:gql|GET_\w+|[A-Z_]+)",
                file_patterns=["*.js", "*.ts", "*.jsx", "*.tsx"],
                type=PatternType.REGEX,
                category=SignatureCategory.FUNCTION_CALL,
                is_definitive=True,
                weight=1.0,
                example="const { loading, data } = useQuery(GET_USERS);",
            ),
        ])
    
    def _add_signature_group(self, framework_name: str, signatures: List[FrameworkSignature]):
        """
        Add a group of signatures for a framework.
        
        Args:
            framework_name: Name of the framework
            signatures: List of signature patterns
        """
        self.signatures[framework_name] = signatures
    
    def _load_patterns_from_registry(self):
        """Load additional patterns from the registry directory."""
        try:
            registry_path = Path(self.pattern_registry_path)
            if not registry_path.exists():
                logger.warning(f"Pattern registry path does not exist: {registry_path}")
                return
            
            for file_path in registry_path.glob("*.json"):
                try:
                    with open(file_path, 'r') as f:
                        pattern_data = json.load(f)
                    
                    framework_name = pattern_data.get("framework")
                    patterns = pattern_data.get("patterns", [])
                    
                    if not framework_name or not patterns:
                        logger.warning(f"Invalid pattern file: {file_path}")
                        continue
                    
                    signatures = []
                    for pattern in patterns:
                        try:
                            signatures.append(FrameworkSignature(**pattern))
                        except Exception as e:
                            logger.warning(f"Invalid pattern in {file_path}: {e}")
                    
                    if framework_name in self.signatures:
                        self.signatures[framework_name].extend(signatures)
                    else:
                        self.signatures[framework_name] = signatures
                    
                    logger.info(f"Loaded {len(signatures)} patterns for {framework_name} from {file_path}")
                
                except Exception as e:
                    logger.warning(f"Error loading pattern file {file_path}: {e}")
        
        except Exception as e:
            logger.warning(f"Error loading patterns from registry: {e}")
    
    def detect_patterns(self, file_info: FileInfo, content: Optional[str] = None) -> List[PatternMatch]:
        """
        Detect framework patterns in a file.
        
        Args:
            file_info: Information about the file
            content: File content (if None, will be read from file_path)
            
        Returns:
            List of pattern matches
        """
        matches = []
        file_path = Path(file_info.full_path)
        
        # Read content if not provided
        if content is None:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                logger.warning(f"Error reading file {file_path}: {e}")
                return matches
        
        # Check each framework's signatures
        for framework_name, framework_signatures in self.signatures.items():
            framework_matches = []
            
            for signature in framework_signatures:
                # Skip if file doesn't match the file pattern
                if not self._match_file_pattern(file_info.path, signature.file_patterns):
                    continue
                
                if signature.type == PatternType.REGEX:
                    # Search for regex pattern
                    try:
                        for match_num, match in enumerate(re.finditer(signature.pattern, content, re.MULTILINE)):
                            # Calculate line number
                            line_num = content[:match.start()].count('\n') + 1
                            
                            # Extract context (line containing the match)
                            line_start = content.rfind('\n', 0, match.start()) + 1
                            line_end = content.find('\n', match.start())
                            if line_end == -1:
                                line_end = len(content)
                            context = content[line_start:line_end].strip()
                            
                            framework_matches.append(
                                PatternMatch(
                                    framework=framework_name,
                                    signature_name=signature.name,
                                    file_path=file_info.path,
                                    line_number=line_num,
                                    context=context,
                                    confidence=signature.weight,
                                    is_definitive=signature.is_definitive,
                                    category=signature.category,
                                )
                            )
                    except Exception as e:
                        logger.warning(f"Error matching pattern {signature.pattern} in {file_path}: {e}")
            
            # Store matches for this framework
            if framework_matches:
                # Add to global matches dictionary
                if framework_name in self.matches:
                    self.matches[framework_name].extend(framework_matches)
                else:
                    self.matches[framework_name] = framework_matches
                
                # Add to result for this file
                matches.extend(framework_matches)
        
        return matches
    
    def detect_patterns_in_files(self, files: List[FileInfo]) -> Dict[str, List[PatternMatch]]:
        """
        Detect patterns in multiple files.
        
        Args:
            files: List of files to analyze
            
        Returns:
            Dictionary mapping file paths to lists of pattern matches
        """
        logger.info(f"Detecting framework patterns in {len(files)} files")
        
        results = {}
        for file_info in files:
            matches = self.detect_patterns(file_info)
            if matches:
                results[file_info.path] = matches
        
        # Log summary of matches
        for framework, matches in self.matches.items():
            logger.info(f"Found {len(matches)} matches for {framework}")
        
        return results
    
    def calculate_framework_confidence(self) -> Dict[str, float]:
        """
        Calculate confidence scores for each detected framework.
        
        Returns:
            Dictionary mapping framework names to confidence scores
        """
        confidence_scores = {}
        
        for framework, matches in self.matches.items():
            if not matches:
                continue
            
            # Weight definitive matches more heavily
            definitive_matches = [m for m in matches if m.is_definitive]
            suggestive_matches = [m for m in matches if not m.is_definitive]
            
            # Calculate base score based on match weights
            definitive_weight = settings.framework_detection.definitive_pattern_weight
            suggestive_weight = settings.framework_detection.suggestive_pattern_weight
            
            definitive_score = sum(m.confidence for m in definitive_matches) * definitive_weight
            suggestive_score = sum(m.confidence for m in suggestive_matches) * suggestive_weight
            
            total_score = definitive_score + suggestive_score
            
            # Normalize to 0-100 scale
            # More matches and more definitive matches increase confidence
            # Apply diminishing returns to avoid extreme scores with many matches
            num_files_with_matches = len(set(m.file_path for m in matches))
            file_diversity_factor = min(1.0, num_files_with_matches / 5)  # Max out at 5 files
            
            # Calculate confidence score
            if definitive_matches:
                # Higher confidence when we have definitive matches
                confidence = min(100, (total_score * file_diversity_factor * 10) + 50)
            else:
                # Lower baseline for only suggestive matches
                confidence = min(80, (total_score * file_diversity_factor * 8) + 20)
            
            confidence_scores[framework] = confidence
        
        return confidence_scores
    
    def get_framework_evidence(self) -> Dict[str, List[Dict]]:
        """
        Get evidence for each detected framework.
        
        Returns:
            Dictionary mapping framework names to lists of evidence
        """
        evidence = {}
        
        for framework, matches in self.matches.items():
            if not matches:
                continue
            
            framework_evidence = []
            
            # Group by file path to avoid too many duplicates from the same file
            by_file = defaultdict(list)
            for match in matches:
                by_file[match.file_path].append(match)
            
            # For each file, include the most relevant evidence
            for file_path, file_matches in by_file.items():
                # Prioritize definitive matches
                definitive = [m for m in file_matches if m.is_definitive]
                
                # Include up to 3 definitive matches per file
                for match in definitive[:3]:
                    framework_evidence.append({
                        "type": "pattern_match",
                        "file_path": match.file_path,
                        "line_number": match.line_number,
                        "context": match.context,
                        "signature": match.signature_name,
                        "confidence": match.confidence,
                        "is_definitive": True,
                    })
                
                # If we don't have 3 definitive matches, add some suggestive ones
                suggestive = [m for m in file_matches if not m.is_definitive]
                remaining_slots = 3 - len(definitive)
                if remaining_slots > 0 and suggestive:
                    for match in suggestive[:remaining_slots]:
                        framework_evidence.append({
                            "type": "pattern_match",
                            "file_path": match.file_path,
                            "line_number": match.line_number,
                            "context": match.context,
                            "signature": match.signature_name,
                            "confidence": match.confidence,
                            "is_definitive": False,
                        })
            
            evidence[framework] = framework_evidence
        
        return evidence
    
    def _match_file_pattern(self, file_path: str, patterns: List[str]) -> bool:
        """
        Check if a file path matches any of the given patterns.
        
        Args:
            file_path: Path to check
            patterns: List of glob patterns to match against
            
        Returns:
            True if the file matches any pattern, False otherwise
        """
        import fnmatch
        
        # If no patterns, match all files
        if not patterns:
            return True
        
        # Check each pattern
        for pattern in patterns:
            if fnmatch.fnmatch(file_path, pattern):
                return True
        
        return False
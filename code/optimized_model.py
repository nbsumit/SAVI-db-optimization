import enum
from sqlalchemy import Index
from . import db
from werkzeug.security import generate_password_hash, check_password_hash

# --- Define Enum types for data integrity and efficiency ---
class UserRoleEnum(enum.Enum):
    pending = 'pending'
    annotator = 'annotator'
    reviewer = 'reviewer'
    admin = 'admin'

class UserStatusEnum(enum.Enum):
    pending = 'pending'
    active = 'active'
    disabled = 'disabled'

class USRStatusEnum(enum.Enum):
    Pending = 'Pending'
    Completed = 'Completed'
    Reviewed = 'Reviewed'

class AnnotationStatusEnum(enum.Enum):
    Unassigned = 'Unassigned'
    Assigned = 'Assigned'
    InProgress = 'InProgress'
    Submitted = 'Submitted'
    Reviewed = 'Reviewed'

class ValidationStatusEnum(enum.Enum):
    pending = 'pending'
    approved = 'approved'
    rejected = 'rejected'
    
class FeedbackStatusEnum(enum.Enum):
    open = 'open'
    in_progress = 'in_progress'
    resolved = 'resolved'
    closed = 'closed'

class FeedbackTypeEnum(enum.Enum):
    issue = 'issue'
    suggestion = 'suggestion'
    question = 'question'

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    # OPTIMIZATION: Index on email for faster lookups during login/registration
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    # OPTIMIZATION: Increased length to 256 to safely store modern secure hashes
    password_hash = db.Column(db.String(256), nullable=False)
    # OPTIMIZATION: Use native Enum for role
    role = db.Column(db.Enum(UserRoleEnum), nullable=False, default=UserRoleEnum.pending, index=True)
    languages = db.Column(db.ARRAY(db.String(50)), nullable=False, default=['hindi'])
    organization = db.Column(db.String(150)) 
    # OPTIMIZATION: Use native Enum for status
    status = db.Column(db.Enum(UserStatusEnum), default=UserStatusEnum.pending, index=True) 
    otp = db.Column(db.String(6), nullable=True)
    otp_expiration = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    annotator_assignments = db.relationship('Assignment', foreign_keys='Assignment.annotator_id', back_populates='annotator', lazy=True, cascade='all, delete-orphan')
    reviewer_assignments = db.relationship('Assignment', foreign_keys='Assignment.reviewer_id', back_populates='reviewer', lazy=True, cascade='all, delete-orphan')

    # OPTIMIZATION: GIN index for fast searching within the 'languages' array
    __table_args__ = (
        Index('ix_user_languages_gin', languages, postgresql_using='gin'),
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Project(db.Model):
    __tablename__ = 'project'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    language = db.Column(db.String(50), nullable=False, default='hindi')
    organization = db.Column(db.String(150)) 
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    chapters = db.relationship('Chapter', back_populates='project', lazy=True, cascade='all, delete-orphan')

class Chapter(db.Model):
    __tablename__ = 'chapter'
    id = db.Column(db.Integer, primary_key=True)
    # OPTIMIZATION: Index on Foreign Key
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(50), nullable=False, default='hindi')
    chapter_text = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    project = db.relationship('Project', back_populates='chapters')
    sentences = db.relationship('Sentence', back_populates='chapter', lazy=True, cascade='all, delete-orphan')

class Sentence(db.Model):
    __tablename__ = 'sentence'
    id = db.Column(db.Integer, primary_key=True)
    # OPTIMIZATION: Index on Foreign Key
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    # OPTIMIZATION: Index on sentence_id for frequent lookups
    sentence_id = db.Column(db.String(100), index=True)
    language = db.Column(db.String(50), nullable=False, default='hindi')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    chapter = db.relationship('Chapter', back_populates='sentences')
    segments = db.relationship('Segment', back_populates='sentence', lazy=True, cascade='all, delete-orphan')

class Segment(db.Model):
    __tablename__ = 'segment'
    id = db.Column(db.Integer, primary_key=True)
    # OPTIMIZATION: Index on Foreign Key
    sentence_id = db.Column(db.Integer, db.ForeignKey('sentence.id'), nullable=False, index=True)
    text = db.Column(db.Text, nullable=False)
    wxtext = db.Column(db.Text)
    englishtext = db.Column(db.Text)
    is_annotated = db.Column(db.Boolean, default=False)
    # OPTIMIZATION: Index on segment_id for frequent lookups
    segment_id = db.Column(db.String(100), index=True)  
    language = db.Column(db.String(50), nullable=False, default='hindi')
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    sentence = db.relationship('Sentence', back_populates='segments')
    usrs = db.relationship('USR', back_populates='segment', lazy=True, cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', back_populates='segment', lazy=True, cascade='all, delete-orphan')
    
    # Note: sentence_type_info is removed from here to fix circular redundancy (Normalization)

class USR(db.Model):
    __tablename__ = 'usr'
    id = db.Column(db.Integer, primary_key=True)
    # OPTIMIZATION: Index on Foreign Key
    segment_id = db.Column(db.Integer, db.ForeignKey('segment.id'), nullable=False, index=True)
    # OPTIMIZATION: Use native Enum for status
    status = db.Column(db.Enum(USRStatusEnum), default=USRStatusEnum.Pending, index=True)
    sentence_type = db.Column(db.String(100))  
    language = db.Column(db.String(50), nullable=False, default='hindi')
    # OPTIMIZATION: Index on Foreign Key
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    segment = db.relationship('Segment', back_populates='usrs')
    lexical_info = db.relationship('LexicalInfo', back_populates='usr', lazy=True, cascade='all, delete-orphan')
    dependency_info = db.relationship('DependencyInfo', back_populates='usr', lazy=True, cascade='all, delete-orphan')
    discourse_coref_info = db.relationship('DiscourseCorefInfo', back_populates='usr', lazy=True, cascade='all, delete-orphan')
    construction_info = db.relationship('ConstructionInfo', back_populates='usr', lazy=True, cascade='all, delete-orphan')
    sentence_type_info = db.relationship('SentenceTypeInfo', back_populates='usr', lazy=True, cascade='all, delete-orphan')

# OPTIMIZATION: Normalization applied to all Info tables below. 
# Removed redundant 'segment_id' column and relationship.
class LexicalInfo(db.Model):
    __tablename__ = 'lexical_info'
    id = db.Column(db.Integer, primary_key=True)
    usr_id = db.Column(db.Integer, db.ForeignKey('usr.id'), nullable=False, index=True)
    concept = db.Column(db.String(100), nullable=False)
    index = db.Column(db.Integer, nullable=False)
    semantic_category = db.Column(db.String(100))
    morpho_semantic = db.Column(db.String(100))
    speakers_view = db.Column(db.String(100))
    usr = db.relationship('USR', back_populates='lexical_info')

class DependencyInfo(db.Model):
    __tablename__ = 'dependency_info'
    id = db.Column(db.Integer, primary_key=True)
    usr_id = db.Column(db.Integer, db.ForeignKey('usr.id'), nullable=False, index=True)
    concept = db.Column(db.String(100), nullable=False)
    index = db.Column(db.Integer, nullable=False)
    head_index = db.Column(db.String(20))
    relation = db.Column(db.String(100), nullable=False)
    usr = db.relationship('USR', back_populates='dependency_info')

class DiscourseCorefInfo(db.Model):
    __tablename__ = 'discourse_coref_info'
    id = db.Column(db.Integer, primary_key=True)
    usr_id = db.Column(db.Integer, db.ForeignKey('usr.id'), nullable=False, index=True)
    concept = db.Column(db.String(100), nullable=False)
    index = db.Column(db.Integer, nullable=False)
    head_index = db.Column(db.String(20))
    relation = db.Column(db.String(100), nullable=False)
    usr = db.relationship('USR', back_populates='discourse_coref_info')

class ConstructionInfo(db.Model):
    __tablename__ = 'construction_info'
    id = db.Column(db.Integer, primary_key=True)
    usr_id = db.Column(db.Integer, db.ForeignKey('usr.id'), nullable=False, index=True)
    concept = db.Column(db.String(100), nullable=False)
    index = db.Column(db.Integer, nullable=False)
    cxn_index = db.Column(db.String(20))
    component_type = db.Column(db.String(100), nullable=False)
    usr = db.relationship('USR', back_populates='construction_info')

class SentenceTypeInfo(db.Model):
    __tablename__ = 'sentence_type_info'
    id = db.Column(db.Integer, primary_key=True)
    usr_id = db.Column(db.Integer, db.ForeignKey('usr.id'), nullable=False, index=True)
    sentence_type = db.Column(db.String(100), nullable=False)
    scope = db.Column(db.String(100))
    usr = db.relationship('USR', back_populates='sentence_type_info')

class Assignment(db.Model):
    __tablename__ = 'assignment'
    id = db.Column(db.Integer, primary_key=True)
    # OPTIMIZATION: Index on Foreign Keys
    segment_id = db.Column(db.Integer, db.ForeignKey('segment.id'), nullable=False, index=True)
    annotator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    reviewer_id = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    feedback = db.Column(db.Text, nullable=True) 
    # OPTIMIZATION: Use native Enum for status
    annotation_status = db.Column(db.Enum(AnnotationStatusEnum), default=AnnotationStatusEnum.Unassigned, index=True)
    assign_lexical = db.Column(db.Boolean, default=False)
    assign_construction = db.Column(db.Boolean, default=False)
    assign_dependency = db.Column(db.Boolean, default=False)
    assign_discourse = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    segment = db.relationship('Segment', back_populates='assignments')
    annotator = db.relationship('User', foreign_keys=[annotator_id], back_populates='annotator_assignments')
    reviewer = db.relationship('User', foreign_keys=[reviewer_id], back_populates='reviewer_assignments')

class Concept(db.Model):
    __tablename__ = 'concept'
    id = db.Column(db.Integer, primary_key=True)
    # OPTIMIZATION: Index on concept_label for fast lookups
    concept_label = db.Column(db.String(200), nullable=False, index=True)  
    hindi_label = db.Column(db.String(200))
    sanskrit_label = db.Column(db.String(200))
    english_label = db.Column(db.String(200)) 
    mrsc = db.Column(db.String(200))  
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class ConceptSubmission(db.Model):
    __tablename__ = 'concept_submission'
    id = db.Column(db.Integer, primary_key=True)
    concept_label = db.Column(db.String(200), nullable=False)
    hindi_label = db.Column(db.String(200), nullable=False)
    sanskrit_label = db.Column(db.String(200))
    english_label = db.Column(db.String(200))
    mrsc = db.Column(db.String(200))
    # OPTIMIZATION: Index on segment_id string
    segment_id = db.Column(db.String(100), index=True)
    original_text = db.Column(db.Text)
    wx_text = db.Column(db.Text)
    english_text = db.Column(db.Text)
    concept_index = db.Column(db.Integer)
    # OPTIMIZATION: Use native Enum for status
    validation_status = db.Column(db.Enum(ValidationStatusEnum), default=ValidationStatusEnum.pending, index=True)
    # OPTIMIZATION: Index on Foreign Keys
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    validated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

class TAM_Dictionary(db.Model):
    __tablename__ = 'tam_dictionary'
    id = db.Column(db.Integer, primary_key=True)
    # OPTIMIZATION: Index on u_tam for fast lookups
    u_tam = db.Column(db.String(255), nullable=False, index=True)
    hindi_tam = db.Column(db.String(255), nullable=False)
    sanskrit_tam = db.Column(db.String(255), nullable=True)
    english_tam = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    def __repr__(self): return f'<TAM_Dictionary {self.id}: {self.u_tam}>'

class TAM_Submission(db.Model):
    __tablename__ = 'tam_submission'
    id = db.Column(db.Integer, primary_key=True)
    u_tam = db.Column(db.String(255), nullable=False)
    hindi_tam = db.Column(db.String(255), nullable=False)
    sanskrit_tam = db.Column(db.String(255), nullable=True)
    english_tam = db.Column(db.String(255), nullable=False)
    # OPTIMIZATION: Index on segment_id string
    segment_id = db.Column(db.String(100), index=True)
    original_text = db.Column(db.Text)
    wx_text = db.Column(db.Text)
    english_text = db.Column(db.Text)
    # OPTIMIZATION: Use native Enum for status
    validation_status = db.Column(db.Enum(ValidationStatusEnum), default=ValidationStatusEnum.pending, index=True)
    # OPTIMIZATION: Index on Foreign Keys
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'), index=True)
    validated_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    feedback = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    def __repr__(self): return f'<TAM_Submission {self.id}: {self.u_tam} ({self.validation_status})>'
    
class SegmentFeedback(db.Model):
    __tablename__ = 'segment_feedback'
    id = db.Column(db.Integer, primary_key=True)
    # OPTIMIZATION: Index on Foreign Keys
    segment_id = db.Column(db.Integer, db.ForeignKey('segment.id'), nullable=False, index=True)
    annotator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    # OPTIMIZATION: Use native Enum
    feedback_type = db.Column(db.Enum(FeedbackTypeEnum), nullable=False)
    feedback_text = db.Column(db.Text, nullable=False)
    # OPTIMIZATION: Use native Enum for status
    status = db.Column(db.Enum(FeedbackStatusEnum), default=FeedbackStatusEnum.open, index=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())
    segment = db.relationship('Segment', backref='feedbacks')
    annotator = db.relationship('User', foreign_keys=[annotator_id])
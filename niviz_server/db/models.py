from __future__ import annotations

import logging

from sqlalchemy import (Column, ForeignKey, Integer, String, Boolean, DateTime,
                        UniqueConstraint)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

logger = logging.getLogger(__name__)

PICTURE_SIZE = 2048
PATH_MAX = 4096

# Permission System


class User(Base):
    '''
    User capable of logging into an application
    '''
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)

    first_name = Column(String(64))
    last_name = Column(String(64))
    username = Column(String(64))
    email = Column(String(64))
    picture = Column(String(PICTURE_SIZE))

    is_active = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    projects = relationship('ProjectUserPermissions', back_populates='user')
    datasets = relationship('DatasetUserPermissions', back_populates='user')


class Project(Base):
    '''
    Niviz Rating project
    '''

    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    users = relationship('ProjectUserPermissions', back_populates='project')


class ProjectUserPermissions(Base):
    '''
    Project-User associations
    '''

    __tablename__ = 'permissions_projectuser'
    __table_args__ = (UniqueConstraint('user_id',
                                       'project_id',
                                       name='unique_project_user'), )

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer,
                     ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False)
    project_id = Column(Integer,
                        ForeignKey('projects.id', ondelete='CASCADE'),
                        nullable=False)

    can_view = Column(Boolean, default=True)
    can_share = Column(Boolean, default=False)
    can_modify = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_admin = Column(Boolean, default=False)

    project = relationship('Projects', back_populates='users')
    user = relationship('Users', back_populates='projects')


class Dataset(Base):
    '''
    A Dataset containing multiple images
    '''
    __tablename__ = 'datasets'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    users = relationship('DatasetUserPermissions', back_populates='dataset')
    entities = relationship('Entity', back_populates='dataset')


class DatasetUserPermissions(Base):
    '''
    Permissions management for Users to Datasets
    '''

    __tablename__ = 'permissions_datasetuser'
    __table_args__ = (UniqueConstraint('user_id',
                                       'dataset_id',
                                       name='unique_dataset_user'), )

    id = Column(Integer, primary_key=True)
    dataset_id = Column(Integer,
                        ForeignKey('datasets.id', ondelete='CASCADE'),
                        nullable=False)
    user_id = Column(Integer,
                     ForeignKey('users.id', ondelete='CASCADE'),
                     nullable=False)

    can_create_project = Column(Boolean, default=False)
    can_view = Column(Boolean, default=True)
    can_share = Column(Boolean, default=False)
    can_modify = Column(Boolean, default=False)
    can_delete = Column(Boolean, default=False)
    can_admin = Column(Boolean, default=False)

    dataset = relationship('Dataset', back_populates='users')
    user = relationship('User', back_populates='datasets')


class ProjectDataset(Base):
    '''
    Records datasets used in QA Projects
    '''

    __tablename__ = 'project_datasets'
    __table_args__ = (UniqueConstraint('project_id',
                                       'dataset_id',
                                       name='unique_project_dataset'), )

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer,
                        ForeignKey('projects.id', ondelete='CASCADE'),
                        nullable=False)
    dataset_id = Column(Integer,
                        ForeignKey('datasets.id', ondelete='CASCADE'),
                        nullable=False)

    project = relationship('Project')
    dataset = relationship('Dataset')


# Entity System


class Entity(Base):
    '''
    Entities representing single scan objects that should be assessed
    for its quality
    '''

    __tablename__ = 'entities'

    id = Column(Integer, primary_key=True)

    dataset_id = Column(ForeignKey("datasets.id", ondelete='CASCADE'),
                        nullable=False)
    updated_at = Column(DateTime)

    dataset = relationship('Dataset', back_populates='entities')
    images = relationship('EntityImage', back_populates='entity')
    metadata = relationship('EntityMetadata', back_populates='entity')


class Metadata(Base):
    '''
    Key-value pairs describing metadata associated with
    a particular entity
    '''
    __tablename__ = 'metadata'

    id = Column(Integer, primary_key=True)
    key_id = Column(Integer,
                    ForeignKey('metadata_keys.id', ondelete='CASCADE'),
                    nullable=False)
    value = Column(String(64))

    key = relationship('MetadataKey')


class MetadataKey(Base):
    '''
    Metadata Keys
    '''

    __tablename__ = 'metadata_keys'
    __table_args__ = (UniqueConstraint('name', name='unique_key_names'), )

    id = Column(Integer, primary_key=True)
    name = Column(String(64))

    metadata = relationship('Metadata', back_populates='key')


class EntityMetadata(Base):
    '''
    Many-to-many between Entity and Metadata
    '''

    __tablename__ = 'entity_metadata'
    __table_args__ = (UniqueConstraint('entity_id',
                                       'metadata_id',
                                       name='unique_entity_metadata'), )

    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer,
                       ForeignKey('entities.id', ondelete='CASCADE'),
                       nullable=False)
    metadata_id = Column(Integer,
                         ForeignKey('metadata.id', ondelete='CASCADE'),
                         nullable=False)

    entity = relationship('Entity', back_populates='metadata')
    metadata = relationship('Metadata')


class Image(Base):
    '''
    QA Image stored in Server's filesystem and used to assess
    the quality of an Entity

    Note that a single image can be used for many Entities
    I.e if a particular pipeline is used for multiple downstream pipelines
    '''

    __tablename__ = 'images'
    __table_args__ = (UniqueConstraint('path', name='unique_image_path'), )

    path = Column(String(PATH_MAX))
    entities = relationship('EntityImage', back_populates='image')


class EntityImage(Base):
    '''
    Association between Entity and Image
    '''

    __tablename__ = 'entity_images'
    __table_args__ = (UniqueConstraint('entity_id',
                                       'image_id',
                                       name='unique_entity_image'), )

    entity_id = Column(Integer,
                       ForeignKey('entities.id', ondelete='CASCADE'),
                       nullable=False)

    image_id = Column(Integer,
                      ForeignKey('images.id', ondelete='CASCADE'),
                      nullable=False)

    image = relationship('Image', back_populates='entities')
    entity = relationship('Entity', back_populates='images')


# Metadata Filtering
class MetadataFilter(Base):
    '''
    Filters applied on Datasets within Projects
    for working on subsets

    '''

    # TODO: Refine how the filter selects for value....?

    __tablename__ = 'metadata_filters'

    id = Column(Integer, primary_key=True)

    project_dataset_id = Column(Integer,
                                ForeignKey(
                                    'project_datasets.id',
                                    ondelete='CASCADE',
                                ),
                                nullable=False)
    metadata_id = Column(Integer,
                         ForeignKey('metadata.id', ondelete='CASCADE'),
                         nullable=False)

    is_exclusion = Column(Boolean, nullable=False, default=False)


# Rating System

# Probably need to break up shit

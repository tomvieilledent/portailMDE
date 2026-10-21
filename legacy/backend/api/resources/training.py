"""Training-related API resources."""

from flask import request
from flask_jwt_extended import get_jwt_identity
from flask_restful import Resource

from backend.api.errors import ERROR_CODES, error_response
from backend.api.jwt_helpers import jwt_required
from backend.api.uploads import (
    delete_uploaded_file, save_document_upload, save_image_upload)
from backend.api.resources._helpers import _can, _cleanup_replaced_upload, _request_payload
from backend.models.training import Training as DomainTraining
from backend.persistence.services import FormationUserService, TrainingService, UserService


training_service = TrainingService()
formation_service = FormationUserService()
user_service = UserService()


def _extract_training_picture(payload):
    uploaded_file = (request.files.get('picture_file')
                     or request.files.get('picture'))
    if uploaded_file and uploaded_file.filename:
        return save_image_upload(uploaded_file, 'trainings')
    return payload.get('picture')


def _extract_uploaded_documents():
    """Save any uploaded attachments and return their public paths.

    Reads every file sent under ``document_file`` (multiple allowed) and stores
    them in ``trainings/documents``. Returns an empty list when none provided.
    """
    saved = []
    for file_storage in request.files.getlist('document_file'):
        if file_storage and file_storage.filename:
            path = save_document_upload(file_storage, 'trainings/documents')
            if path:
                saved.append(path)
    return saved


class TrainingListResource(Resource):
    """List trainings or create a new training (super admin only)."""

    @jwt_required()
    def get(self):
        """Return a list of trainings.

        Query parameters:
            limit (int): Max trainings to return (default 100).

        Returns:
            tuple[dict, int]: ``{trainings}`` and 200.
        """
        limit = request.args.get('limit', default=100, type=int)
        return {'trainings': training_service.facade.list(limit=limit)}

    @jwt_required()
    def post(self):
        """Create a training. Restricted to super admins.

        Expected body (JSON or multipart):
            title (str): Training title (required).
            description (str | None): Optional description.
            picture (str | None): Optional picture path/URL.
            company_id (str | None): Optional owning company UUID.
            category (str | None): Optional free-text category.
            type (str | None): ``'formation'`` (default) or ``'atelier'``.
            document_file (file | None): One or more attachments (multipart).

        Returns:
            tuple[dict, int]: ``{training}`` and 201, or 403.
        """
        current_user = user_service.get_by_id(get_jwt_identity())
        if not current_user:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        if not _can(current_user, 'manage_trainings'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to create trainings', 403)
        data = _request_payload()
        picture = _extract_training_picture(data)
        title = data.get('title')
        if not title:
            return error_response(ERROR_CODES['BAD_REQUEST'], 'title is required', 400)
        try:
            domain = DomainTraining(
                title=title, description=data.get('description'),
                picture=picture, company_id=data.get('company_id'),
                category=data.get('category'), type=data.get('type'))
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)
        documents = _extract_uploaded_documents()
        try:
            training = training_service.facade.create(
                title,
                company_id=data.get('company_id'),
                description=data.get('description'),
                picture=picture,
                category=domain.category,
                type=domain.type,
                documents=documents,
            )
        except Exception as exc:
            return error_response(ERROR_CODES['CONFLICT'], 'could not create training', 409, str(exc))
        return {'training': training}, 201


class TrainingResource(Resource):
    """Retrieve, update or deactivate a single training."""

    @jwt_required()
    def get(self, training_id):
        """Return a training by id.

        Args:
            training_id (str): Training UUID path parameter.

        Returns:
            tuple[dict, int]: ``{training}`` and 200, or 404.
        """
        training = training_service.facade.get(training_id)
        if not training:
            return error_response(ERROR_CODES['NOT_FOUND'], 'training not found', 404)
        return {'training': training}

    @jwt_required()
    def patch(self, training_id):
        """Partially update a training's fields.

        Args:
            training_id (str): Training UUID path parameter.

        Returns:
            tuple[dict, int]: ``{training}`` and 200.
        """
        data = _request_payload()
        update_data: dict[str, object] = {}

        current = training_service.facade.get(training_id)
        if not current:
            return error_response(ERROR_CODES['NOT_FOUND'], 'training not found', 404)
        previous_picture = current.get('picture')

        try:
            domain = DomainTraining(
                title=current.get('title'),
                description=current.get('description'),
                picture=current.get('picture'),
                company_id=current.get('company_id'),
                category=current.get('category'),
                type=current.get('type'),
            )
            for k, v in data.items():
                if hasattr(domain, k):
                    setattr(domain, k, v)
            uploaded_file = (request.files.get('picture_file')
                             or request.files.get('picture'))
            if uploaded_file and uploaded_file.filename:
                update_data['picture'] = save_image_upload(uploaded_file, 'trainings')
            elif 'picture' in data:
                update_data['picture'] = data.get('picture')
            for field in ('title', 'description', 'company_id', 'is_active'):
                if field in data:
                    update_data[field] = data.get(field)
            # Normalised category/type come from the validated domain object.
            if 'category' in data:
                update_data['category'] = domain.category
            if 'type' in data:
                update_data['type'] = domain.type
            # Newly uploaded attachments are appended to the existing list.
            new_documents = _extract_uploaded_documents()
            if new_documents:
                update_data['documents'] = (current.get('documents') or []) + new_documents
        except Exception as exc:
            return error_response(ERROR_CODES['VALIDATION_ERROR'], str(exc), 400)

        training = training_service.facade.update(training_id, **update_data)
        if not training:
            return error_response(ERROR_CODES['NOT_FOUND'], 'training not found', 404)
        _cleanup_replaced_upload(previous_picture, update_data.get('picture'))
        return {'training': training}

    @jwt_required()
    def delete(self, training_id):
        """Soft-deactivate a training.

        Args:
            training_id (str): Training UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, or 404.
        """
        if not training_service.facade.deactivate(training_id, by=get_jwt_identity()):
            return error_response(ERROR_CODES['NOT_FOUND'], 'training not found', 404)
        return {'msg': 'training deactivated'}


class TrainingDocumentResource(Resource):
    """Remove a single attachment from a training (super admin only)."""

    @jwt_required()
    def delete(self, training_id):
        """Detach a document and delete its file.

        Args:
            training_id (str): Training UUID path parameter.

        Expected JSON body:
            path (str): Public path of the attachment to remove.

        Returns:
            tuple[dict, int]: ``{training}`` and 200, or 400/403/404.
        """
        current_user = user_service.get_by_id(get_jwt_identity())
        if not _can(current_user, 'manage_trainings'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to manage training documents', 403)
        data = request.get_json(silent=True) or {}
        path = data.get('path')
        if not path:
            return error_response(ERROR_CODES['BAD_REQUEST'], 'path is required', 400)
        current = training_service.facade.get(training_id)
        if not current:
            return error_response(ERROR_CODES['NOT_FOUND'], 'training not found', 404)
        documents = current.get('documents') or []
        if path not in documents:
            return error_response(ERROR_CODES['NOT_FOUND'], 'document not found', 404)
        remaining = [d for d in documents if d != path]
        training = training_service.facade.update(training_id, documents=remaining)
        delete_uploaded_file(path)
        return {'training': training}


class TrainingInterestResource(Resource):
    """Express or withdraw interest in a training (for unscheduled sessions)."""

    @jwt_required()
    def post(self, training_id):
        """Express interest in a training.

        Creates an ``interested`` FormationUser record. Idempotent — calling
        again returns the existing record.

        Args:
            training_id (str): Training UUID path parameter.

        Returns:
            tuple[dict, int]: ``{interest}`` and 201, or 404.
        """
        if not training_service.facade.get(training_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'training not found', 404)
        result = formation_service.facade.express_interest(
            get_jwt_identity(), training_id)
        return {'interest': result}, 201

    @jwt_required()
    def delete(self, training_id):
        """Remove interest in a training.

        Args:
            training_id (str): Training UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, or 404.
        """
        if not training_service.facade.get(training_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'training not found', 404)
        if not formation_service.facade.remove_interest(
                get_jwt_identity(), training_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'interest not found', 404)
        return {'msg': 'interest removed'}


class TrainingSavedResource(Resource):
    """Bookmark or remove a training from the current user's saved list."""

    @jwt_required()
    def post(self, training_id):
        """Bookmark a training for the current user.

        Creates (or reuses) a FormationUser row with ``saved=True``,
        independently of any interest/enrollment state. Idempotent.

        Args:
            training_id (str): Training UUID path parameter.

        Returns:
            tuple[dict, int]: ``{saved}`` and 201, or 404.
        """
        if not training_service.facade.get(training_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'training not found', 404)
        result = formation_service.facade.save_training(
            get_jwt_identity(), training_id)
        return {'saved': result}, 201

    @jwt_required()
    def delete(self, training_id):
        """Remove a training from the current user's saved list.

        Args:
            training_id (str): Training UUID path parameter.

        Returns:
            tuple[dict, int]: ``{msg}`` and 200, or 404.
        """
        if not training_service.facade.get(training_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'training not found', 404)
        if not formation_service.facade.unsave_training(
                get_jwt_identity(), training_id):
            return error_response(ERROR_CODES['NOT_FOUND'], 'saved training not found', 404)
        return {'msg': 'training unsaved'}


class CurrentUserSavedTrainingsResource(Resource):
    """List the trainings bookmarked by the currently authenticated user."""

    @jwt_required()
    def get(self):
        """Return the current user's saved trainings.

        Returns:
            tuple[dict, int]: ``{saved}`` and 200.
        """
        return {'saved': formation_service.facade.list_saved(get_jwt_identity())}


class TrainingEnrollmentsResource(Resource):
    """List enrollments for a given training."""

    @jwt_required()
    def get(self, training_id):
        """Return enrollments for a training, optionally filtered by type.

        Args:
            training_id (str): Training UUID path parameter.

        Query parameters:
            type (str): Filter by ``interested``, ``enrolled``, or
                ``completed``.

        Returns:
            tuple[dict, int]: ``{enrollments}`` and 200, or 404.
        """
        current_user = user_service.get_by_id(get_jwt_identity())
        if not _can(current_user, 'manage_trainings'):
            return error_response(
                ERROR_CODES['FORBIDDEN'],
                'not allowed to view enrollments', 403)
        training = training_service.facade.get(training_id)
        if not training:
            return error_response(ERROR_CODES['NOT_FOUND'], 'training not found', 404)
        type_filter = request.args.get('type')
        return {'enrollments': formation_service.facade.list_by_training(
            training_id, type_filter=type_filter)}


class UserTrainingsResource(Resource):
    """List enrollments for a specific user."""

    @jwt_required()
    def get(self, user_id):
        """Return enrollments for a user.

        Args:
            user_id (str): User UUID path parameter.

        Query parameters:
            type (str): Filter by ``interested``, ``enrolled``, or
                ``completed``.

        Returns:
            tuple[dict, int]: ``{enrollments}`` and 200, or 404.
        """
        user = user_service.get_by_id(user_id)
        if not user:
            return error_response(ERROR_CODES['NOT_FOUND'], 'user not found', 404)
        type_filter = request.args.get('type')
        return {'enrollments': formation_service.facade.list_by_user(
            user_id, type_filter=type_filter)}


class CurrentUserTrainingsResource(Resource):
    """List enrollments for the currently authenticated user."""

    @jwt_required()
    def get(self):
        """Return the current user's enrollments.

        Query parameters:
            type (str): Filter by ``interested``, ``enrolled``, or
                ``completed``.

        Returns:
            tuple[dict, int]: ``{enrollments}`` and 200.
        """
        type_filter = request.args.get('type')
        return {'enrollments': formation_service.facade.list_by_user(
            get_jwt_identity(), type_filter=type_filter)}

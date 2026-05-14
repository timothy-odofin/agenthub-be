"""
App API registry: defines app APIs the agent can call. Backend executes the HTTP call
using base_url (config APP_API_BASE_URL) and Authorization header from the incoming
request (user's token forwarded to the main app).
"""

import json
import re
import urllib.parse
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Tuple

# Registry: api, method, path (use {id} etc. for path params), payload_keys, description.
# For GET: payload becomes query params. Path params are extracted from payload and substituted in path.
APP_API_REGISTRY: List[Dict[str, Any]] = [
    # ---- Clients ----
    {
        "api": "create_client",
        "method": "POST",
        "path": "/clients",
        "payload_keys": ["name", "email", "phone", "address"],
        "description": "Create a new client. Payload: name (required), email (required), phone (optional), address (optional).",
    },
    {
        "api": "list_clients",
        "method": "GET",
        "path": "/clients",
        "payload_keys": ["page", "limit", "search", "status", "sort", "order"],
        "description": "List clients with optional pagination and filters. Payload: page, limit, search, status (active|inactive), sort, order.",
    },
    {
        "api": "get_client",
        "method": "GET",
        "path": "/clients/{id}",
        "payload_keys": ["id"],
        "description": "Get a client by id.",
    },
    {
        "api": "update_client",
        "method": "PUT",
        "path": "/clients/{id}",
        "payload_keys": ["id", "name", "email", "phone", "address"],
        "description": "Update a client. Payload: id (required), name, email, phone, address (optional).",
    },
    {
        "api": "update_client_status",
        "method": "PATCH",
        "path": "/clients/{id}/status",
        "payload_keys": ["id", "status"],
        "description": "Update client status. Payload: id (required), status (active|inactive).",
    },
    {
        "api": "delete_client",
        "method": "DELETE",
        "path": "/clients/{id}",
        "payload_keys": ["id"],
        "description": "Delete a client by id.",
    },
    {
        "api": "get_client_stats",
        "method": "GET",
        "path": "/clients/stats",
        "payload_keys": [],
        "description": "Get client statistics (total, active, inactive).",
    },
    {
        "api": "get_client_activities",
        "method": "GET",
        "path": "/clients/{id}/activities",
        "payload_keys": ["id"],
        "description": "Get activity history for a client. Payload: id (client id).",
    },
    # ---- Suppliers ----
    {
        "api": "create_supplier",
        "method": "POST",
        "path": "/suppliers",
        "payload_keys": ["name", "email", "phone", "address"],
        "description": "Create a new supplier. Payload: name (required), email (required), phone (optional), address (optional).",
    },
    {
        "api": "list_suppliers",
        "method": "GET",
        "path": "/suppliers",
        "payload_keys": ["page", "limit", "search", "status", "sort", "order"],
        "description": "List suppliers with optional pagination and filters.",
    },
    {
        "api": "get_supplier",
        "method": "GET",
        "path": "/suppliers/{id}",
        "payload_keys": ["id"],
        "description": "Get a supplier by id.",
    },
    {
        "api": "update_supplier",
        "method": "PUT",
        "path": "/suppliers/{id}",
        "payload_keys": ["id", "name", "email", "phone", "address", "status"],
        "description": "Update a supplier. Payload: id (required), name, email, phone, address, status (optional).",
    },
    {
        "api": "delete_supplier",
        "method": "DELETE",
        "path": "/suppliers/{id}",
        "payload_keys": ["id"],
        "description": "Delete a supplier by id.",
    },
    {
        "api": "get_supplier_stats",
        "method": "GET",
        "path": "/suppliers/stats",
        "payload_keys": [],
        "description": "Get supplier statistics.",
    },
    {
        "api": "add_supplier_resource",
        "method": "POST",
        "path": "/suppliers/{supplierId}/resources",
        "payload_keys": ["supplierId", "resourceId", "unitPrice", "leadTimeDays", "minimumOrderQuantity", "notes"],
        "description": "Add a resource to a supplier. Payload: supplierId, resourceId, unitPrice; optional: leadTimeDays, minimumOrderQuantity, notes.",
    },
    {
        "api": "remove_supplier_resource",
        "method": "DELETE",
        "path": "/suppliers/{supplierId}/resources/{resourceId}",
        "payload_keys": ["supplierId", "resourceId"],
        "description": "Remove a resource from a supplier.",
    },
    # ---- Resources ----
    {
        "api": "create_resource",
        "method": "POST",
        "path": "/resources",
        "payload_keys": ["name", "resourceType", "unit", "currency", "description", "elementTags", "tags", "basePrice", "categoryId", "supplierId", "status"],
        "description": "Create a resource (material, labor, or equipment). Payload: name, resourceType (MATERIAL|LABOR|EQUIPMENT), unit, currency; optional: description, elementTags, tags, basePrice, categoryId, supplierId, status.",
    },
    {
        "api": "list_resources",
        "method": "GET",
        "path": "/resources",
        "payload_keys": ["page", "limit", "search", "resourceType", "status", "categoryId", "supplierId"],
        "description": "List resources with optional filters.",
    },
    {
        "api": "get_resource",
        "method": "GET",
        "path": "/resources/{id}",
        "payload_keys": ["id"],
        "description": "Get a resource by id.",
    },
    {
        "api": "update_resource",
        "method": "PUT",
        "path": "/resources/{id}",
        "payload_keys": ["id", "name", "resourceType", "unit", "currency", "description", "elementTags", "tags", "basePrice", "categoryId", "supplierId", "status"],
        "description": "Update a resource. Payload: id (required), then any fields to update.",
    },
    {
        "api": "delete_resource",
        "method": "DELETE",
        "path": "/resources/{id}",
        "payload_keys": ["id"],
        "description": "Delete a resource by id.",
    },
    {
        "api": "get_resource_stats",
        "method": "GET",
        "path": "/resources/stats",
        "payload_keys": [],
        "description": "Get resource statistics.",
    },
    # ---- Users ----
    {
        "api": "list_users",
        "method": "GET",
        "path": "/users",
        "payload_keys": ["page", "limit"],
        "description": "List users with pagination.",
    },
    {
        "api": "get_user",
        "method": "GET",
        "path": "/users/{id}",
        "payload_keys": ["id"],
        "description": "Get a user by id.",
    },
    {
        "api": "update_user",
        "method": "PUT",
        "path": "/users/{id}",
        "payload_keys": ["id", "fullName", "email", "phone", "roleId"],
        "description": "Update a user. Payload: id (required), fullName, email, phone, roleId (optional).",
    },
    # ---- Invitations ----
    {
        "api": "invite_user",
        "method": "POST",
        "path": "/invitations",
        "payload_keys": ["email", "name", "role"],
        "description": "Invite a user by email. Payload: email (required), name (required), role (admin, project_manager, estimator, viewer).",
    },
    {
        "api": "list_invitations",
        "method": "GET",
        "path": "/invitations",
        "payload_keys": ["status", "email", "roleId"],
        "description": "List invitations with optional filters.",
    },
    {
        "api": "get_invitation",
        "method": "GET",
        "path": "/invitations/{id}",
        "payload_keys": ["id"],
        "description": "Get an invitation by id.",
    },
    {
        "api": "resend_invitation",
        "method": "POST",
        "path": "/invitations/{id}/resend",
        "payload_keys": ["id"],
        "description": "Resend an invitation by id.",
    },
    {
        "api": "revoke_invitation",
        "method": "PUT",
        "path": "/invitations/{id}/revoke",
        "payload_keys": ["id", "reason"],
        "description": "Revoke an invitation. Payload: id (required), reason (optional).",
    },
    {
        "api": "cancel_invitation",
        "method": "DELETE",
        "path": "/invitations/{id}",
        "payload_keys": ["id"],
        "description": "Cancel/delete an invitation by id.",
    },
    # ---- Market surveys ----
    {
        "api": "create_market_survey",
        "method": "POST",
        "path": "/market-surveys",
        "payload_keys": ["resourceId", "surveyDate", "location", "notes", "status"],
        "description": "Create a market survey. Payload: resourceId (required), surveyDate (required), location, notes, status (optional).",
    },
    {
        "api": "list_market_surveys",
        "method": "GET",
        "path": "/market-surveys",
        "payload_keys": ["page", "limit", "search", "status", "resourceId", "sort", "order"],
        "description": "List market surveys with optional filters.",
    },
    {
        "api": "get_market_survey",
        "method": "GET",
        "path": "/market-surveys/{id}",
        "payload_keys": ["id"],
        "description": "Get a market survey by id.",
    },
    {
        "api": "update_market_survey",
        "method": "PUT",
        "path": "/market-surveys/{id}",
        "payload_keys": ["id", "resourceId", "surveyDate", "location", "notes", "status"],
        "description": "Update a market survey.",
    },
    {
        "api": "delete_market_survey",
        "method": "DELETE",
        "path": "/market-surveys/{id}",
        "payload_keys": ["id"],
        "description": "Delete a market survey by id.",
    },
    {
        "api": "get_market_survey_stats",
        "method": "GET",
        "path": "/market-surveys/stats",
        "payload_keys": [],
        "description": "Get market survey statistics.",
    },
    {
        "api": "add_market_survey_supplier",
        "method": "POST",
        "path": "/market-surveys/{marketSurveyId}/suppliers",
        "payload_keys": ["marketSurveyId", "supplierId", "unitPrice", "leadTimeDays", "minimumOrderQuantity", "notes"],
        "description": "Add a supplier rate to a market survey.",
    },
    {
        "api": "update_market_survey_supplier_rate",
        "method": "PUT",
        "path": "/market-surveys/{marketSurveyId}/suppliers/{supplierId}",
        "payload_keys": ["marketSurveyId", "supplierId", "unitPrice", "leadTimeDays", "minimumOrderQuantity", "notes"],
        "description": "Update a supplier rate on a market survey.",
    },
    {
        "api": "remove_market_survey_supplier",
        "method": "DELETE",
        "path": "/market-surveys/{marketSurveyId}/suppliers/{supplierId}",
        "payload_keys": ["marketSurveyId", "supplierId"],
        "description": "Remove a supplier from a market survey.",
    },
    # ---- BOQ Drafts (status=DRAFT — single table boq_projects) ----
    {
        "api": "create_boq_draft",
        "method": "POST",
        "path": "/boq/drafts",
        "payload_keys": ["projectType", "creationMethod", "documentTitle", "currentStep", "projectInfo"],
        "description": "Create a new BOQ draft. Required: projectType ('BOQ'|'QUOTE'). Optional: creationMethod ('AI'|'MANUAL'), documentTitle, currentStep (1-6), projectInfo ({projectName, location, description, client: {id, name?, contact?}, clientName (deprecated)}).",
    },
    {
        "api": "get_boq_draft",
        "method": "GET",
        "path": "/boq/drafts/{id}",
        "payload_keys": ["id"],
        "description": "Get a BOQ draft by id.",
    },
    {
        "api": "list_my_boq_drafts",
        "method": "GET",
        "path": "/boq/drafts/my-drafts",
        "payload_keys": [],
        "description": "List all draft BOQ documents for the current user.",
    },
    {
        "api": "update_boq_draft",
        "method": "PATCH",
        "path": "/boq/drafts/{id}/v2",
        "payload_keys": ["id", "documentTitle", "projectInfo", "templateId", "templateName", "templateSource", "creationMethod", "elements"],
        "description": "Update a BOQ draft (v2 endpoint). Payload: id (required), plus any fields to update: documentTitle, projectInfo ({name,location,description,clientName}), templateId, templateName, templateSource, creationMethod, elements (array of {elementId,description,quantity,unit,rate,dimensions}).",
    },
    {
        "api": "delete_boq_draft",
        "method": "DELETE",
        "path": "/boq/drafts/{id}",
        "payload_keys": ["id"],
        "description": "Delete a BOQ draft by id.",
    },
    # ---- BOQ Projects (status=PENDING|APPROVED) ----
    {
        "api": "list_boq_projects",
        "method": "GET",
        "path": "/boq/projects",
        "payload_keys": ["page", "limit", "search", "status"],
        "description": "List all BOQ documents (drafts, pending, approved). Optional filters: page, limit, search, status (DRAFT|PENDING|APPROVED).",
    },
    {
        "api": "get_boq_project",
        "method": "GET",
        "path": "/boq/projects/{id}",
        "payload_keys": ["id"],
        "description": "Get a BOQ project by id.",
    },
    {
        "api": "submit_boq_for_review",
        "method": "POST",
        "path": "/boq/projects/v2",
        "payload_keys": ["draftId"],
        "description": "Submit a BOQ draft for review (changes status from DRAFT to PENDING). Payload: draftId (required).",
    },
    {
        "api": "update_boq_project_status",
        "method": "PATCH",
        "path": "/boq/projects/{id}/status",
        "payload_keys": ["id", "status"],
        "description": "Update the status of a BOQ project. Payload: id (required), status (APPROVED|REJECTED|PENDING).",
    },
    {
        "api": "get_boq_project_preview",
        "method": "GET",
        "path": "/boq/projects/{id}/preview",
        "payload_keys": ["id"],
        "description": "Get a preview of a BOQ project with all elements and calculated totals.",
    },
    {
        "api": "update_boq_project_item",
        "method": "PATCH",
        "path": "/boq/projects/{projectId}/items/{itemId}",
        "payload_keys": ["projectId", "itemId", "description", "quantity", "rate", "dimensions"],
        "description": "Update an item within a BOQ project.",
    },
    {
        "api": "delete_boq_project_item",
        "method": "DELETE",
        "path": "/boq/projects/{projectId}/items/{itemId}",
        "payload_keys": ["projectId", "itemId"],
        "description": "Delete an item from a BOQ project.",
    },
    # ---- BOQ Items (inline creation via boq.controller) ----
    {
        "api": "create_boq_item",
        "method": "POST",
        "path": "/boq/items",
        "payload_keys": ["projectId", "elementId", "description", "quantity", "unit", "rate", "dimensions"],
        "description": "Create a single BOQ item within a project. Payload: projectId (required), elementId (required), description, quantity, unit, rate, dimensions.",
    },
    {
        "api": "bulk_create_boq_items",
        "method": "POST",
        "path": "/boq/items/bulk",
        "payload_keys": ["projectId", "items"],
        "description": "Bulk create BOQ items within a project. Payload: projectId (required), items (array of {elementId, description, quantity, unit, rate, dimensions}).",
    },
    # ---- BOQ Standards — Construction Types (templates) ----
    {
        "api": "list_construction_types",
        "method": "GET",
        "path": "/boq/standards/construction-types-paginated",
        "payload_keys": ["page", "limit", "search", "isActive"],
        "description": "List available construction type templates with pagination. Use this to let the user pick a BOQ template.",
    },
    {
        "api": "get_construction_type_elements",
        "method": "GET",
        "path": "/boq/standards/construction-types/{id}/elements-paginated",
        "payload_keys": ["id", "page", "limit"],
        "description": "Get the BOQ elements (line items) for a construction type template. Payload: id (construction type id, required).",
    },
    # ---- BOQ Elements ----
    {
        "api": "list_boq_elements",
        "method": "GET",
        "path": "/boq/elements",
        "payload_keys": ["stageId", "substageId", "includeSystemDefaults"],
        "description": "List BOQ elements. Optional: stageId, substageId, includeSystemDefaults.",
    },
    {
        "api": "get_boq_element",
        "method": "GET",
        "path": "/boq/elements/{id}",
        "payload_keys": ["id"],
        "description": "Get a BOQ element by id.",
    },
    {
        "api": "create_boq_element",
        "method": "POST",
        "path": "/boq/elements",
        "payload_keys": ["stageId", "substageId", "name", "code", "description", "unit", "calculationMethod", "isActive"],
        "description": "Create a BOQ element.",
    },
    {
        "api": "update_boq_element",
        "method": "PUT",
        "path": "/boq/elements/{id}",
        "payload_keys": ["id", "name", "code", "description", "unit", "calculationMethod", "isActive"],
        "description": "Update a BOQ element.",
    },
    {
        "api": "delete_boq_element",
        "method": "DELETE",
        "path": "/boq/elements/{id}",
        "payload_keys": ["id"],
        "description": "Delete a BOQ element by id.",
    },
    {
        "api": "adopt_boq_element",
        "method": "POST",
        "path": "/boq/elements/{id}/adopt",
        "payload_keys": ["id"],
        "description": "Adopt a system default element to tenant.",
    },
    {
        "api": "list_boq_element_resources",
        "method": "GET",
        "path": "/boq/elements/{elementId}/resources",
        "payload_keys": ["elementId"],
        "description": "List resources linked to a BOQ element.",
    },
    {
        "api": "create_boq_element_resource",
        "method": "POST",
        "path": "/boq/elements/{elementId}/resources",
        "payload_keys": ["elementId", "resourceType", "resourceName", "quantityPerUnit", "unit", "rate", "wasteFactor"],
        "description": "Add a resource to a BOQ element.",
    },
    {
        "api": "update_boq_element_resource",
        "method": "PUT",
        "path": "/boq/elements/{elementId}/resources/{resourceId}",
        "payload_keys": ["elementId", "resourceId", "quantityPerUnit", "rate", "wasteFactor"],
        "description": "Update an element resource.",
    },
    {
        "api": "delete_boq_element_resource",
        "method": "DELETE",
        "path": "/boq/elements/{elementId}/resources/{resourceId}",
        "payload_keys": ["elementId", "resourceId"],
        "description": "Remove a resource from a BOQ element.",
    },
    # ---- BOQ Standards (stages, substages, construction types) ----
    {
        "api": "list_boq_stages",
        "method": "GET",
        "path": "/boq/standards/stages",
        "payload_keys": ["includeSystemDefaults"],
        "description": "List construction stages. Optional: includeSystemDefaults.",
    },
    {
        "api": "get_boq_stage",
        "method": "GET",
        "path": "/boq/standards/stages/{id}",
        "payload_keys": ["id"],
        "description": "Get a construction stage by id.",
    },
    {
        "api": "create_boq_stage",
        "method": "POST",
        "path": "/boq/standards/stages",
        "payload_keys": ["name", "code", "description", "displayOrder", "stageLevel", "parentStageId"],
        "description": "Create a construction stage.",
    },
    {
        "api": "update_boq_stage",
        "method": "PUT",
        "path": "/boq/standards/stages/{id}",
        "payload_keys": ["id", "name", "code", "description", "displayOrder", "stageLevel", "parentStageId"],
        "description": "Update a construction stage.",
    },
    {
        "api": "delete_boq_stage",
        "method": "DELETE",
        "path": "/boq/standards/stages/{id}",
        "payload_keys": ["id"],
        "description": "Delete a construction stage by id.",
    },
    {
        "api": "adopt_boq_stage",
        "method": "POST",
        "path": "/boq/standards/stages/{id}/adopt",
        "payload_keys": ["id"],
        "description": "Adopt a system default stage to tenant.",
    },
    {
        "api": "list_boq_substages",
        "method": "GET",
        "path": "/boq/standards/substages",
        "payload_keys": ["stageId"],
        "description": "List substages. Optional: stageId.",
    },
    {
        "api": "create_boq_substage",
        "method": "POST",
        "path": "/boq/standards/substages",
        "payload_keys": ["stageId", "name", "code", "description", "displayOrder"],
        "description": "Create a substage.",
    },
    {
        "api": "update_boq_substage",
        "method": "PUT",
        "path": "/boq/standards/substages/{id}",
        "payload_keys": ["id", "name", "code", "description", "displayOrder"],
        "description": "Update a substage.",
    },
    {
        "api": "delete_boq_substage",
        "method": "DELETE",
        "path": "/boq/standards/substages/{id}",
        "payload_keys": ["id"],
        "description": "Delete a substage by id.",
    },
    {
        "api": "list_boq_construction_types",
        "method": "GET",
        "path": "/boq/standards/construction-types",
        "payload_keys": ["includeSystemDefaults"],
        "description": "List construction types.",
    },
    {
        "api": "get_boq_construction_type",
        "method": "GET",
        "path": "/boq/standards/construction-types/{id}",
        "payload_keys": ["id"],
        "description": "Get a construction type by id.",
    },
    {
        "api": "create_boq_construction_type",
        "method": "POST",
        "path": "/boq/standards/construction-types",
        "payload_keys": ["typeCode", "typeName", "description", "category"],
        "description": "Create a construction type. category: RESIDENTIAL|COMMERCIAL|INDUSTRIAL|INSTITUTIONAL|GENERAL.",
    },
    {
        "api": "update_boq_construction_type",
        "method": "PUT",
        "path": "/boq/standards/construction-types/{id}",
        "payload_keys": ["id", "typeCode", "typeName", "description", "category"],
        "description": "Update a construction type.",
    },
    {
        "api": "delete_boq_construction_type",
        "method": "DELETE",
        "path": "/boq/standards/construction-types/{id}",
        "payload_keys": ["id"],
        "description": "Delete a construction type by id.",
    },
    {
        "api": "adopt_boq_construction_type",
        "method": "POST",
        "path": "/boq/standards/construction-types/{id}/adopt",
        "payload_keys": ["id"],
        "description": "Adopt a system default construction type to tenant.",
    },
    # ---- BOQ Templates (dimensions, mix-ratios) ----
    {
        "api": "list_boq_dimension_templates",
        "method": "GET",
        "path": "/boq/templates/dimensions",
        "payload_keys": ["elementId"],
        "description": "List dimension templates. Optional: elementId.",
    },
    {
        "api": "create_boq_dimension_template",
        "method": "POST",
        "path": "/boq/templates/dimensions",
        "payload_keys": ["name", "elementId", "dimensions", "isDefault"],
        "description": "Create a dimension template.",
    },
    {
        "api": "update_boq_dimension_template",
        "method": "PUT",
        "path": "/boq/templates/dimensions/{id}",
        "payload_keys": ["id", "name", "elementId", "dimensions", "isDefault"],
        "description": "Update a dimension template.",
    },
    {
        "api": "delete_boq_dimension_template",
        "method": "DELETE",
        "path": "/boq/templates/dimensions/{id}",
        "payload_keys": ["id"],
        "description": "Delete a dimension template by id.",
    },
    {
        "api": "list_boq_mix_ratios",
        "method": "GET",
        "path": "/boq/templates/mix-ratios",
        "payload_keys": [],
        "description": "List mix ratio templates.",
    },
    {
        "api": "create_boq_mix_ratio",
        "method": "POST",
        "path": "/boq/templates/mix-ratios",
        "payload_keys": ["name", "concreteGrade", "cementBags", "sharpSand", "granite", "water", "unit"],
        "description": "Create a mix ratio template.",
    },
    {
        "api": "calculate_boq_mix_ratio",
        "method": "POST",
        "path": "/boq/templates/mix-ratios/calculate",
        "payload_keys": ["mixRatioId", "volume"],
        "description": "Calculate mix ratio quantities for a volume. Payload: mixRatioId, volume.",
    },
    # ---- Search ----
    {
        "api": "search_global",
        "method": "GET",
        "path": "/search/global",
        "payload_keys": ["query", "limit", "entityTypes"],
        "description": "Global search across entities. Payload: query (required), limit, entityTypes.",
    },
    {
        "api": "search_clients",
        "method": "GET",
        "path": "/search/clients",
        "payload_keys": ["query", "limit"],
        "description": "Search clients. Payload: query (required), limit.",
    },
    {
        "api": "search_suppliers",
        "method": "GET",
        "path": "/search/suppliers",
        "payload_keys": ["query", "limit"],
        "description": "Search suppliers.",
    },
    {
        "api": "search_resources",
        "method": "GET",
        "path": "/search/resources",
        "payload_keys": ["query", "limit"],
        "description": "Search resources.",
    },
    {
        "api": "search_projects",
        "method": "GET",
        "path": "/search/projects",
        "payload_keys": ["query", "limit"],
        "description": "Search BOQ projects.",
    },
    # ---- Analytics ----
    {
        "api": "get_analytics_overview",
        "method": "GET",
        "path": "/analytics/overview",
        "payload_keys": ["startDate", "endDate"],
        "description": "Get analytics overview. Optional: startDate, endDate.",
    },
    {
        "api": "get_recent_activity",
        "method": "GET",
        "path": "/analytics/recent-activity",
        "payload_keys": ["limit"],
        "description": "Get recent activity. Optional: limit.",
    },
    {
        "api": "get_trends",
        "method": "GET",
        "path": "/analytics/trends",
        "payload_keys": ["metric", "period"],
        "description": "Get trend data. Payload: metric, period.",
    },
    # ---- Files ----
    {
        "api": "list_files",
        "method": "GET",
        "path": "/files",
        "payload_keys": ["page", "limit", "categoryId", "search"],
        "description": "List files with optional filters.",
    },
    {
        "api": "get_file",
        "method": "GET",
        "path": "/files/{id}",
        "payload_keys": ["id"],
        "description": "Get file metadata by id.",
    },
    {
        "api": "delete_file",
        "method": "DELETE",
        "path": "/files/{id}",
        "payload_keys": ["id"],
        "description": "Delete a file by id.",
    },
    {
        "api": "list_file_categories",
        "method": "GET",
        "path": "/files/categories",
        "payload_keys": [],
        "description": "List file categories.",
    },
    {
        "api": "create_file_category",
        "method": "POST",
        "path": "/files/categories",
        "payload_keys": ["name", "description", "maxSize", "allowedExtensions"],
        "description": "Create a file category.",
    },
    {
        "api": "associate_file",
        "method": "POST",
        "path": "/files/{fileId}/associate",
        "payload_keys": ["fileId", "entityType", "entityId", "associationType"],
        "description": "Associate a file with an entity. Payload: fileId, entityType, entityId, associationType (optional).",
    },
    {
        "api": "get_files_by_entity",
        "method": "GET",
        "path": "/files/entity/{entityType}/{entityId}",
        "payload_keys": ["entityType", "entityId"],
        "description": "Get files associated with an entity.",
    },
    # ---- Lookups (for dropdowns / options) ----
    {
        "api": "lookup_clients",
        "method": "GET",
        "path": "/lookups/clients",
        "payload_keys": ["search", "limit"],
        "description": "Lookup clients for dropdown/autocomplete.",
    },
    {
        "api": "lookup_suppliers",
        "method": "GET",
        "path": "/lookups/suppliers",
        "payload_keys": ["search", "limit"],
        "description": "Lookup suppliers.",
    },
    {
        "api": "lookup_resources",
        "method": "GET",
        "path": "/lookups/resources",
        "payload_keys": ["search", "limit", "resourceType"],
        "description": "Lookup resources.",
    },
    {
        "api": "lookup_users",
        "method": "GET",
        "path": "/lookups/users",
        "payload_keys": ["search", "limit", "roleId"],
        "description": "Lookup users.",
    },
    {
        "api": "lookup_locations",
        "method": "GET",
        "path": "/lookups/locations",
        "payload_keys": ["search", "limit"],
        "description": "Lookup project locations (Nigerian states / cities) for dropdown.",
    },
    {
        "api": "lookup_market_surveys",
        "method": "GET",
        "path": "/lookups/market-surveys",
        "payload_keys": ["search", "limit"],
        "description": "Lookup market surveys.",
    },
    {
        "api": "lookup_banks",
        "method": "GET",
        "path": "/lookups/banks",
        "payload_keys": ["search", "limit"],
        "description": "Lookup banks.",
    },
    # ---- Company settings ----
    {
        "api": "get_company_settings",
        "method": "GET",
        "path": "/settings/company",
        "payload_keys": [],
        "description": "Get company settings.",
    },
    {
        "api": "update_company_settings",
        "method": "PUT",
        "path": "/settings/company",
        "payload_keys": ["name", "email", "phone", "address", "website", "logoUrl"],
        "description": "Update company settings.",
    },
    {
        "api": "list_bank_accounts",
        "method": "GET",
        "path": "/settings/company/bank-accounts",
        "payload_keys": [],
        "description": "List company bank accounts.",
    },
    {
        "api": "create_bank_account",
        "method": "POST",
        "path": "/settings/company/bank-accounts",
        "payload_keys": ["bankName", "accountName", "accountNumber", "sortCode", "currency", "isDefault"],
        "description": "Create a bank account.",
    },
    {
        "api": "get_bank_account",
        "method": "GET",
        "path": "/settings/company/bank-accounts/{id}",
        "payload_keys": ["id"],
        "description": "Get a bank account by id.",
    },
    {
        "api": "update_bank_account",
        "method": "PUT",
        "path": "/settings/company/bank-accounts/{id}",
        "payload_keys": ["id", "bankName", "accountName", "accountNumber", "sortCode", "currency", "isDefault"],
        "description": "Update a bank account.",
    },
    {
        "api": "delete_bank_account",
        "method": "DELETE",
        "path": "/settings/company/bank-accounts/{id}",
        "payload_keys": ["id"],
        "description": "Delete a bank account by id.",
    },
    {
        "api": "set_default_bank_account",
        "method": "PUT",
        "path": "/settings/company/bank-accounts/{id}/set-default",
        "payload_keys": ["id"],
        "description": "Set default bank account.",
    },
    # ---- Terms & conditions ----
    {
        "api": "list_terms_categories",
        "method": "GET",
        "path": "/settings/terms/categories",
        "payload_keys": [],
        "description": "List terms and conditions categories.",
    },
    {
        "api": "create_terms_category",
        "method": "POST",
        "path": "/settings/terms/categories",
        "payload_keys": ["name", "description"],
        "description": "Create a terms category.",
    },
    {
        "api": "update_terms_category",
        "method": "PUT",
        "path": "/settings/terms/categories/{id}",
        "payload_keys": ["id", "name", "description"],
        "description": "Update a terms category.",
    },
    {
        "api": "delete_terms_category",
        "method": "DELETE",
        "path": "/settings/terms/categories/{id}",
        "payload_keys": ["id"],
        "description": "Delete a terms category by id.",
    },
    {
        "api": "list_terms",
        "method": "GET",
        "path": "/settings/terms",
        "payload_keys": ["categoryId", "approvalStatus", "isActive"],
        "description": "List terms and conditions. Optional: categoryId, approvalStatus, isActive.",
    },
    {
        "api": "get_default_terms",
        "method": "GET",
        "path": "/settings/terms/default",
        "payload_keys": [],
        "description": "Get default terms and conditions.",
    },
    {
        "api": "create_terms",
        "method": "POST",
        "path": "/settings/terms",
        "payload_keys": ["categoryId", "title", "content", "version", "isActive"],
        "description": "Create terms and conditions.",
    },
    {
        "api": "get_terms",
        "method": "GET",
        "path": "/settings/terms/{id}",
        "payload_keys": ["id"],
        "description": "Get terms by id.",
    },
    {
        "api": "update_terms",
        "method": "PUT",
        "path": "/settings/terms/{id}",
        "payload_keys": ["id", "title", "content", "version", "isActive"],
        "description": "Update terms and conditions.",
    },
    {
        "api": "delete_terms",
        "method": "DELETE",
        "path": "/settings/terms/{id}",
        "payload_keys": ["id"],
        "description": "Delete terms by id.",
    },
    {
        "api": "set_default_terms",
        "method": "POST",
        "path": "/settings/terms/{id}/set-default",
        "payload_keys": ["id"],
        "description": "Set default terms by id.",
    },
    {
        "api": "approve_terms",
        "method": "POST",
        "path": "/settings/terms/{id}/approve",
        "payload_keys": ["id", "comments"],
        "description": "Approve terms. Payload: id (required), comments (optional).",
    },
]


def get_payload_keys_for_api(api: str) -> List[str]:
    """Return payload keys for LLM extraction for the given API."""
    for entry in APP_API_REGISTRY:
        if entry.get("api") == api:
            return list(entry.get("payload_keys", []))
    return []


def get_registry_entry(api: str) -> Optional[Dict[str, Any]]:
    """Return full registry entry for an API, or None."""
    for entry in APP_API_REGISTRY:
        if entry.get("api") == api:
            return entry
    return None


def list_app_apis() -> List[str]:
    """Return list of registered API keys for call_app_api."""
    return [e["api"] for e in APP_API_REGISTRY if e.get("api")]


def _normalize_phone(payload: Dict[str, Any]) -> Tuple[str, str]:
    """Return (phone_national, phone_country_code) from payload.phone."""
    raw = (payload.get("phone") or "").strip()
    if not raw:
        return "", "234"
    match = re.match(r"^\+?(\d{1,4})\s*(.+)$", raw)
    if match:
        return re.sub(r"\D", "", match.group(2)), re.sub(r"\D", "", match.group(1)) or "234"
    return re.sub(r"\D", "", raw), "234"


def _normalize_payload_for_api(api: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize LLM-extracted payload to the shape the app API expects."""
    if api == "create_client":
        name = str(payload.get("name") or "").strip()
        email = str(payload.get("email") or "").strip()
        address = (payload.get("address") or "").strip() or None
        phone_nat, phone_cc = _normalize_phone(payload)
        return {
            "name": name,
            "email": email,
            "phone": phone_nat or None,
            "phoneCountryCode": phone_cc,
            "address": address,
        }
    if api == "create_supplier":
        name = str(payload.get("name") or "").strip()
        email = str(payload.get("email") or "").strip()
        address = (payload.get("address") or "").strip() or None
        phone_nat, phone_cc = _normalize_phone(payload)
        return {
            "name": name,
            "email": email,
            "phone": phone_nat or None,
            "phoneCountryCode": phone_cc,
            "address": address,
        }
    if api == "invite_user":
        role = str(payload.get("role") or "").strip().lower().replace(" ", "_")
        return {
            "email": str(payload.get("email") or "").strip(),
            "name": str(payload.get("name") or "").strip(),
            "role": role,
        }
    if api == "create_resource":
        rt = str(payload.get("resourceType") or "MATERIAL").upper()
        if rt not in ("MATERIAL", "LABOR", "EQUIPMENT"):
            rt = "MATERIAL"
        element_tags = payload.get("elementTags")
        if isinstance(element_tags, list):
            element_tags = [str(x) for x in element_tags]
        elif element_tags is not None:
            element_tags = [str(element_tags)]
        else:
            element_tags = []
        tags = payload.get("tags")
        if isinstance(tags, list):
            tags = [str(x) for x in tags]
        elif tags is not None:
            tags = [str(tags)]
        else:
            tags = []
        out = {
            "name": str(payload.get("name") or "").strip(),
            "resourceType": rt,
            "unit": str(payload.get("unit") or "").strip(),
            "currency": str(payload.get("currency") or "NGN").strip(),
            "elementTags": element_tags,
            "tags": tags,
        }
        if payload.get("description") is not None:
            out["description"] = str(payload["description"]).strip()
        if payload.get("basePrice") is not None:
            try:
                out["basePrice"] = float(payload["basePrice"])
            except (TypeError, ValueError):
                pass
        if payload.get("categoryId") is not None:
            out["categoryId"] = str(payload["categoryId"]).strip()
        if payload.get("supplierId") is not None:
            out["supplierId"] = str(payload["supplierId"]).strip()
        if payload.get("status") is not None:
            out["status"] = str(payload["status"]).strip().lower()
        return out
    return dict(payload)


def _path_params_from_template(path_template: str) -> List[str]:
    """Extract {param} names from path template."""
    return re.findall(r"\{(\w+)\}", path_template)


def _build_path_and_payload(
    path_template: str,
    payload: Dict[str, Any],
    method: str,
) -> Tuple[str, Dict[str, Any]]:
    """
    Substitute path params from payload; return (final_path, remaining_payload).
    Remaining payload: for GET used as query params; for POST/PUT/PATCH used as body (minus path param keys).
    """
    path_params = _path_params_from_template(path_template)
    path_values = {}
    for k in path_params:
        v = payload.get(k)
        if v is not None and v != "":
            path_values[k] = str(v).strip()
    path = path_template
    for k, v in path_values.items():
        path = path.replace("{" + k + "}", urllib.parse.quote(str(v), safe=""))
    remaining = {k: v for k, v in payload.items() if k not in path_params and v is not None}
    return path, remaining


def execute_app_api(
    api: str,
    payload: Dict[str, Any],
    auth_header: Optional[str],
    base_url: str,
) -> Tuple[bool, Optional[Dict[str, Any]], str]:
    """
    Execute the app API call from the backend. Look up registry for method/path,
    normalize payload, substitute path params, send HTTP request.
    GET: no body, payload (after path substitution) as query string.
    DELETE: no body (or empty).
    PUT/PATCH/POST: remaining payload as JSON body.
    Returns (success, data, message).
    """
    entry = get_registry_entry(api)
    if not entry:
        return False, None, f"Unknown API: {api}"

    method = (entry.get("method") or "GET").upper()
    path_template = (entry.get("path") or "").strip().lstrip("/")
    path, remaining = _build_path_and_payload(path_template, payload or {}, method)

    url = f"{base_url.rstrip('/')}/{path}"

    if method == "GET":
        if remaining:
            # Encode query params; skip None/empty, stringify values for query
            q = {}
            for k, v in remaining.items():
                if v is None or v == "":
                    continue
                if isinstance(v, bool):
                    q[k] = "true" if v else "false"
                elif isinstance(v, (list, dict)):
                    q[k] = json.dumps(v)
                else:
                    q[k] = str(v)
            if q:
                query_string = urllib.parse.urlencode(q)
                url = f"{url}?{query_string}"
        body_bytes = None
        headers = {"Accept": "application/json"}
    else:
        body = _normalize_payload_for_api(api, remaining) if remaining else {}
        body_bytes = json.dumps(body).encode("utf-8") if body else None
        headers = {"Content-Type": "application/json", "Accept": "application/json"}

    if auth_header:
        headers["Authorization"] = auth_header

    try:
        req = urllib.request.Request(url, data=body_bytes, method=method, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            code = resp.getcode()
            raw = resp.read().decode("utf-8")
            try:
                parsed = json.loads(raw) if raw else {}
            except json.JSONDecodeError:
                parsed = {}
            if code >= 200 and code < 300:
                data_obj = parsed.get("data") if isinstance(parsed.get("data"), (dict, list)) else parsed
                return True, data_obj, "Success"
            return False, None, parsed.get("message") or raw or f"HTTP {code}"
    except urllib.error.HTTPError as e:
        try:
            err_body = e.read().decode("utf-8")
            err_json = json.loads(err_body)
            msg = err_json.get("message") or err_json.get("error") or err_body
        except Exception:
            msg = str(e)
        return False, None, msg
    except Exception as e:
        return False, None, str(e)
# usage sample: from app.agent.app_api_registry import execute_app_api
#  result = await _call_api("list_clients", {"page": 1, "limit": 50}, state)
# async def _call_api(api_name: str, payload: dict, state: CostPlanningState) -> dict:
#     from config import config as _config
#     auth_token = state.get("auth_token", "")
#     base_url = _config.APP_API_BASE_URL
#     loop = asyncio.get_event_loop()
#     success, data, message = await loop.run_in_executor(
#         None,
#         lambda: execute_app_api(api_name, payload, auth_token, base_url),
#     )
#     if not success:
#         raise RuntimeError(f"{api_name} failed: {message}")
#     return {"data": data, "message": message}

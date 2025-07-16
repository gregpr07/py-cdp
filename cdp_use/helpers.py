"""
Helper utilities for common CDP operations.

This module provides convenience functions to reduce boilerplate when working
with Chrome DevTools Protocol responses.
"""

from typing import Any, TypeVar, cast
from cdp_use.cdp.runtime.commands import EvaluateReturns
from cdp_use.cdp.runtime.types import ExceptionDetails
from cdp_use.cdp.dom.commands import GetBoxModelReturns, ResolveNodeReturns
from cdp_use.cdp.page.commands import GetNavigationHistoryReturns


T = TypeVar('T')


class CDPError(Exception):
	"""Base exception for CDP-related errors."""
	pass


class CDPEvaluationError(CDPError):
	"""Raised when CDP evaluation fails."""
	def __init__(self, exception_details: ExceptionDetails):
		self.exception_details = exception_details
		super().__init__(f"CDP evaluation failed: {exception_details}")


class CDPResponseError(CDPError):
	"""Raised when CDP response is missing expected data."""
	pass


# Runtime helpers

def extract_value(evaluate_result: EvaluateReturns, default: T | None = None) -> T | None:
	"""
	Extract value from Runtime.evaluate result with proper type handling.
	
	Args:
		evaluate_result: The result from Runtime.evaluate
		default: Default value to return if no value is found
		
	Returns:
		The extracted value or default
		
	Raises:
		CDPEvaluationError: If the evaluation resulted in an exception
	"""
	if 'exceptionDetails' in evaluate_result:
		raise CDPEvaluationError(evaluate_result['exceptionDetails'])
	
	if 'result' in evaluate_result:
		remote_obj = evaluate_result['result']
		if 'value' in remote_obj:
			return cast(T, remote_obj['value'])
	
	return default


def extract_object_id(evaluate_result: EvaluateReturns) -> str | None:
	"""
	Extract objectId from Runtime.evaluate result.
	
	Args:
		evaluate_result: The result from Runtime.evaluate
		
	Returns:
		The objectId if present, None otherwise
		
	Raises:
		CDPEvaluationError: If the evaluation resulted in an exception
	"""
	if 'exceptionDetails' in evaluate_result:
		raise CDPEvaluationError(evaluate_result['exceptionDetails'])
	
	if 'result' in evaluate_result and 'objectId' in evaluate_result['result']:
		return evaluate_result['result']['objectId']
	return None


async def evaluate_expression(cdp_client, expression: str, session_id: str | None = None) -> Any:
	"""
	Evaluate JavaScript expression and return value directly.
	
	Args:
		cdp_client: The CDP client instance
		expression: JavaScript expression to evaluate
		session_id: Optional session ID for the evaluation context
		
	Returns:
		The evaluated value
		
	Raises:
		CDPEvaluationError: If the evaluation fails
	"""
	result: EvaluateReturns = await cdp_client.send.Runtime.evaluate(
		params={'expression': expression, 'returnByValue': True},
		session_id=session_id
	)
	return extract_value(result)


async def evaluate_with_object(cdp_client, expression: str, session_id: str | None = None) -> str:
	"""
	Evaluate JavaScript expression and return objectId.
	
	Args:
		cdp_client: The CDP client instance
		expression: JavaScript expression to evaluate
		session_id: Optional session ID for the evaluation context
		
	Returns:
		The objectId of the evaluated expression
		
	Raises:
		CDPEvaluationError: If the evaluation fails
		CDPResponseError: If no objectId is returned
	"""
	result: EvaluateReturns = await cdp_client.send.Runtime.evaluate(
		params={'expression': expression},
		session_id=session_id
	)
	object_id = extract_object_id(result)
	if not object_id:
		raise CDPResponseError(f"No objectId returned for expression: {expression}")
	return object_id


# DOM helpers

def extract_box_model(box_model_result: GetBoxModelReturns) -> dict[str, Any]:
	"""
	Extract box model from DOM.getBoxModel result.
	
	Args:
		box_model_result: The result from DOM.getBoxModel
		
	Returns:
		The box model dictionary
		
	Raises:
		CDPResponseError: If no box model is present
	"""
	if 'model' not in box_model_result:
		raise CDPResponseError("No box model returned")
	return box_model_result['model']


async def get_element_box(cdp_client, backend_node_id: int, session_id: str | None = None) -> dict[str, Any]:
	"""
	Get element box model with proper error handling.
	
	Args:
		cdp_client: The CDP client instance
		backend_node_id: The backend node ID
		session_id: Optional session ID
		
	Returns:
		The box model dictionary
		
	Raises:
		CDPResponseError: If no box model is returned
	"""
	result: GetBoxModelReturns = await cdp_client.send.DOM.getBoxModel(
		params={'backendNodeId': backend_node_id},
		session_id=session_id
	)
	return extract_box_model(result)


# Page helpers

def extract_navigation_history(history_result: GetNavigationHistoryReturns) -> tuple[int, list[dict[str, Any]]]:
	"""
	Extract current index and entries from navigation history.
	
	Args:
		history_result: The result from Page.getNavigationHistory
		
	Returns:
		Tuple of (currentIndex, entries)
	"""
	current_index = history_result.get('currentIndex', 0)
	entries = history_result.get('entries', [])
	return current_index, entries


# Context managers

from contextlib import asynccontextmanager

@asynccontextmanager
async def cdp_session(cdp_client, target_id: str):
	"""
	Context manager for CDP sessions.
	
	Usage:
		async with cdp_session(cdp_client, target_id) as session_id:
			# Use session_id in CDP commands
			await cdp_client.send.Runtime.evaluate(..., session_id=session_id)
	"""
	result = await cdp_client.send.Target.attachToTarget(
		params={'targetId': target_id, 'flatten': True}
	)
	session_id = result['sessionId']
	try:
		yield session_id
	finally:
		try:
			await cdp_client.send.Target.detachFromTarget(
				params={'sessionId': session_id}
			)
		except Exception:
			# Session might already be detached
			pass
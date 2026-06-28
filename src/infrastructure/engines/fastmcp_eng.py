import logging
import asyncio
from typing import List
from src.domain.services import BrowserEngine

logger = logging.getLogger("flight_scraper")

class FastMcpEngine(BrowserEngine):
    def __init__(self, server_url: str, auth_token: str):
        self.server_url = server_url
        self.auth_token = auth_token
        self.client = None
        self.tools = []

    def start(self) -> None:
        logger.info(f"Connecting to FastMCP Stealth Browser at: {self.server_url}...")
        try:
            from fastmcp import Client
            from fastmcp.client.auth import BearerAuth
            
            self.client = Client(
                self.server_url,
                auth=BearerAuth(self.auth_token),
            )
            self.tools = self.client.list_tools()
            tool_names = [t.name for t in self.tools]
            logger.info(f"Connected successfully. Available MCP tools: {tool_names}")
        except Exception as e:
            logger.error(f"Failed to connect to FastMCP server: {e}")
            raise

    def _call_browser_tool(self, possible_names: List[str], **kwargs):
        if not self.client:
            raise RuntimeError("FastMCP client session not started.")
            
        matched_name = None
        for name in possible_names:
            if any(t.name == name for t in self.tools):
                matched_name = name
                break
                
        if not matched_name:
            matched_name = possible_names[0]
            logger.warning(f"No exact tool match found. Trying fallback tool name: {matched_name}")
            
        try:
            return self.client.call_tool(matched_name, **kwargs)
        except Exception as e:
            logger.error(f"Error calling MCP tool '{matched_name}': {e}")
            raise

    def navigate(self, url: str) -> None:
        logger.info(f"MCP Navigating to: {url}")
        self._call_browser_tool(["navigate", "goto", "open_url"], url=url)

    def get_title(self) -> str:
        try:
            return self.evaluate_js("document.title")
        except Exception:
            try:
                return self._call_browser_tool(["get_title"])
            except Exception:
                return ""

    def get_body_text(self) -> str:
        try:
            return self.evaluate_js("document.body.innerText")
        except Exception:
            try:
                return self._call_browser_tool(["get_body", "get_text"])
            except Exception:
                return ""

    def evaluate_js(self, script: str) -> str:
        response = self._call_browser_tool(
            ["evaluate", "evaluate_javascript", "execute_script", "js_eval"],
            script=script
        )
        return str(response)

    def get_elements_text_by_xpath(self, xpath: str) -> List[str]:
        js_code = f"""
        (() => {{
            const result = [];
            const nodesSnapshot = document.evaluate(
                "{xpath}", 
                document, 
                null, 
                XPathResult.ORDERED_NODE_SNAPSHOT_TYPE, 
                null
            );
            for (let i = 0; i < nodesSnapshot.snapshotLength; i++) {{
                const val = nodesSnapshot.snapshotItem(i).textContent;
                if (val) result.push(val.trim());
            }}
            return JSON.stringify(result);
        }})()
        """
        try:
            raw_result = self.evaluate_js(js_code)
            import json
            return json.loads(raw_result)
        except Exception as e:
            logger.error(f"Failed to query elements by XPath via FastMCP: {e}")
            return []

    def find_parent_with_xpath_child_text(self, child_xpath: str, target_xpath: str, max_depth: int = 10) -> str:
        js_code = f"""
        (() => {{
            const childElement = document.evaluate(
                "{child_xpath}", 
                document, 
                null, 
                XPathResult.FIRST_ORDERED_NODE_TYPE, 
                null
            ).singleNodeValue;
            
            if (!childElement) return "N/A";
            
            let current = childElement;
            for (let i = 0; i < {max_depth}; i++) {{
                current = current.parentElement;
                if (!current) break;
                
                const target = document.evaluate(
                    "{target_xpath}", 
                    current, 
                    null, 
                    XPathResult.FIRST_ORDERED_NODE_TYPE, 
                    null
                ).singleNodeValue;
                
                if (target) return target.textContent.trim();
            }}
            return "N/A";
        }})()
        """
        try:
            return self.evaluate_js(js_code)
        except Exception as e:
            logger.error(f"Failed to find parent child text via FastMCP: {e}")
            return "N/A"

    def check_exists_by_xpath(self, xpath: str) -> bool:
        js_code = f"""
        (() => {{
            const element = document.evaluate(
                "{xpath}", 
                document, 
                null, 
                XPathResult.FIRST_ORDERED_NODE_TYPE, 
                null
            ).singleNodeValue;
            return !!element;
        }})()
        """
        try:
            return self.evaluate_js(js_code).lower() == "true"
        except Exception:
            return False

    def close(self) -> None:
        logger.info("Disconnecting FastMCP client session...")
        self.client = None

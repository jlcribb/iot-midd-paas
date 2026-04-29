"""Convenience entry point for running DTE API locally."""

from __future__ import annotations

import uvicorn


def main() -> None:
    uvicorn.run("iot_middleware.dte.api.app:app", host="0.0.0.0", port=8010, reload=False)


if __name__ == "__main__":
    main()

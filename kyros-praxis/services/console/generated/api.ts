/* eslint-disable */
export interface paths {
  "/jobs": {
    get: {
      parameters: {};
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["JobArray"];
          };
        };
      };
    };
    post: {
      parameters: {};
      requestBody: {
        content: {
          "application/json": components["schemas"]["CreateJob"];
        };
      };
      responses: {
        201: {
          content: {
            "application/json": components["schemas"]["Job"];
          };
        };
      };
    };
  };
  "/services": {
    get: {
      parameters: {};
      responses: {
        200: {
          content: {
            "application/json": components["schemas"]["ServiceArray"];
          };
        };
      };
    };
  };
}

export interface components {
  schemas: {
    Job: {
      type: "object";
      properties: {
        id: {
          type: "string";
        };
        status: {
          type: "string";
        };
        created_at: {
          type: "string";
        };
      };
    };
    JobArray: {
      type: "array";
      items: components["schemas"]["Job"];
    };
    Service: {
      type: "object";
      properties: {
        id: {
          type: "string";
        };
        name: {
          type: "string";
        };
        status: {
          type: "string";
        };
      };
    };
    ServiceArray: {
      type: "array";
      items: components["schemas"]["Service"];
    };
    CreateJob: {
      type: "object";
      properties: {
        source_type: {
          type: "string";
        };
        source_payload: {
          type: "object";
        };
      };
    };
  };
}

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export const api = {
  getJobs: async (): Promise<components["schemas"]["JobArray"]> => {
    const response = await fetch(`${BASE_URL}/jobs`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },
  createJob: async (body: components["schemas"]["CreateJob"]): Promise<components["schemas"]["Job"]> => {
    const response = await fetch(`${BASE_URL}/jobs`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },
  getServices: async (): Promise<components["schemas"]["ServiceArray"]> => {
    const response = await fetch(`${BASE_URL}/services`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return response.json();
  },
};
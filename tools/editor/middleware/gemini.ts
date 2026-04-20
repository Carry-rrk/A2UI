/*
 * Copyright 2025 Google LLC
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      https://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

import { IncomingMessage, ServerResponse } from "http";
import { Plugin, ViteDevServer } from "vite";
import { v0_8 } from "@a2ui/lit";
import { createA2UIPrompt } from "./prompts";

let catalog: v0_8.Types.ClientCapabilitiesDynamic | null = null;

/**
 * Custom LLM handler that supports OpenAI-compatible APIs (like vLLM)
 */
export const plugin = (): Plugin => {
  const baseUrl = process.env.LLM_BASE_URL || "http://localhost:8082/v1";
  const modelName = process.env.LLM_MODEL_NAME || "Qwen3.5-35B-A3B";
  const apiKey = process.env.LLM_API_KEY || "not-needed";

  return {
    name: "custom-gemini-handler", // Kept name for compatibility with imports
    configureServer(server: ViteDevServer) {
      server.middlewares.use(
        "/a2ui",
        async (req: IncomingMessage, res: ServerResponse, next: () => void) => {
          if (req.method === "POST") {
            let contents = "";

            req.on("data", (chunk) => {
              contents += chunk.toString();
            });

            req.on("end", async () => {
              try {
                const payload = JSON.parse(
                  contents
                ) as v0_8.Types.A2UIClientEventMessage;

                if (payload.clientUiCapabilities || payload.userAction) {
                  if (payload.clientUiCapabilities) {
                    if ("dynamicCatalog" in payload.clientUiCapabilities) {
                      catalog = payload.clientUiCapabilities.dynamicCatalog;

                      res.statusCode = 200;
                      res.setHeader("Content-Type", "application/json");
                      res.end(
                        JSON.stringify({
                          role: "assistant",
                          parts: [{ text: "Dynamic Catalog Received" }],
                        })
                      );
                      return;
                    }
                  } else if (payload.userAction) {
                    return;
                  }
                } else {
                  if (!payload.request || !catalog) {
                    res.statusCode = 400;
                    res.setHeader("Content-Type", "application/json");
                    res.end(
                      JSON.stringify({
                        error: `Invalid message - No payload or catalog`,
                      })
                    );
                    return;
                  }

                  if (v0_8.Data.Guards.isObject(payload.request)) {
                    const request = payload.request as {
                      imageData?: string;
                      instructions: string;
                    };

                    // For now, we assume simple text instructions as most local vLLMs 
                    // might need specific setup for multimodal. 
                    // We ignore imageDescription or set it to empty if vLLM is text-only.
                    let imageDescription = "";
                    if (request.imageData) {
                      imageDescription = "[Image provided]";
                    }

                    const promptObj = createA2UIPrompt(
                      catalog,
                      imageDescription,
                      request.instructions
                    );

                    // Convert Gemini-style prompt parts to a single string for OpenAI chat completions
                    const userMessageContent = promptObj.parts.map(p => p.text).join("\n\n");

                    const completionResponse = await fetch(`${baseUrl}/chat/completions`, {
                      method: "POST",
                      headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${apiKey}`
                      },
                      body: JSON.stringify({
                        model: modelName,
                        messages: [
                          {
                            role: "system",
                            content: `Please return a valid array
                            necessary to satisfy the user request. If no data is
                            provided create some. If there are any URLs you must
                            make them absolute and begin with a /.

                            Nothing should ever be loaded from a remote source.

                            You are working as part of an AI system, so no chit-chat and
                            no explaining what you're doing and why.DO NOT start with
                            "Okay", or "Alright" or any preambles. Just the output,
                            please.

                            ULTRA IMPORTANT: *Just* return the A2UI Protocol
                            Message object, do not wrap it in markdown. Just the object
                            please, nothing else!`
                          },
                          {
                            role: "user",
                            content: userMessageContent
                          }
                        ],
                        temperature: 0.1 // Lower temperature for structured output
                      })
                    });

                    if (!completionResponse.ok) {
                      const errorData = await completionResponse.text();
                      throw new Error(`LLM API error: ${errorData}`);
                    }

                    const completionJson = await completionResponse.json();
                    const responseText = completionJson.choices[0].message.content;

                    res.statusCode = 200;
                    res.setHeader("Content-Type", "application/json");
                    res.end(
                      JSON.stringify({
                        role: "assistant",
                        parts: [{ text: responseText }],
                      })
                    );
                  } else {
                    throw new Error("Expected request to be an object");
                  }
                }
              } catch (err) {
                res.statusCode = 400;
                res.setHeader("Content-Type", "application/json");
                res.end(
                  JSON.stringify({
                    error: `Invalid message - ${err}`,
                  })
                );
              }
            });

            return;
          } else {
            next();
          }
        }
      );
    },
  };
};

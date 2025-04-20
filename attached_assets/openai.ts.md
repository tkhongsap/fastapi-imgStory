import OpenAI from "openai";
import { z } from "zod";
import * as dotenv from "dotenv";
import * as fs from "fs";
import * as path from "path";

// Load environment variables
dotenv.config();

// API key is now hardcoded so we don't need to check for environment variables
// NOTE: This is a temporary approach for development only

// For project-based keys, we'll use the specified model
const VISION_MODEL = "gpt-4.1-mini";  // Primary vision model
const FALLBACK_VISION_MODEL = "gpt-4.1-mini";  // Same fallback model
let activeVisionModel = VISION_MODEL;

// Flag to indicate if we're in fallback mode (no OpenAI API)
let usingFallbackMode = false;

// Read API key from environment variable
const apiKey = process.env.OPENAI_API_KEY || "";

// Check if API key is available
if (!apiKey) {
  console.error("⚠️ OPENAI_API_KEY environment variable is not set");
}

// Extract first 7 chars and last 4 chars for better identification, keeping middle private
const keyPreview =
  apiKey.substring(0, 7) + "..." + apiKey.substring(apiKey.length - 4);
console.log(`OpenAI API key: ${keyPreview}`);

// Check if using a project-based API key
const isProjectBasedKey = apiKey.startsWith("sk-proj-");
console.log(
  `Using ${isProjectBasedKey ? "project-based" : "standard"} OpenAI API key`,
);

// Initialize OpenAI client with full configuration
export const openai = new OpenAI({
  apiKey: apiKey, // Using OPENAI_API_KEY from environment variables
  organization: process.env.OPENAI_ORG_ID, // Optional, in case it's needed
  dangerouslyAllowBrowser: false,
  defaultQuery: {
    // For project-based API keys (sk-proj), ensure we're using the needed parameters
    ...(isProjectBasedKey
      ? { organization: process.env.OPENAI_ORG_ID || undefined }
      : {}),
  },
  defaultHeaders: {
    // Add beta features flag if needed
    "OpenAI-Beta": "assistants=v1",
  },
});

// Verify API key works and check which models are available
async function verifyApiKey() {
  try {
    // First try with a simpler API call for project-based keys
    if (isProjectBasedKey) {
      try {
        // For project-based keys, try with gpt-4.1-mini as specified
        const response = await openai.chat.completions.create({
          model: "gpt-4.1-mini",
          messages: [{ role: "user", content: "Test" }],
          max_tokens: 5,
        });

        if (response) {
          console.log(
            "✅ Project-based OpenAI API key validated successfully.",
          );
          // Use gpt-4.1-mini for project-based key as specified
          activeVisionModel = "gpt-4.1-mini";
          console.log(
            `Using vision model for project-based key: ${activeVisionModel}`,
          );
          return true;
        }
      } catch (projError: any) {
        // If this fails too, fall through to standard error handling
        console.warn(
          "Project-based key validation failed, trying standard validation...",
        );
      }
    }

    // Make a standard API call to test the key and get available models
    const models = await openai.models.list();
    console.log("✅ OpenAI API key validated successfully.");

    // Check which vision models are available
    const availableModels = models.data.map((model) => model.id);

    if (availableModels.includes(VISION_MODEL)) {
      console.log(`Using preferred vision model: ${VISION_MODEL}`);
      activeVisionModel = VISION_MODEL;
    } else if (availableModels.includes(FALLBACK_VISION_MODEL)) {
      console.log(
        `Preferred model ${VISION_MODEL} not available, using fallback: ${FALLBACK_VISION_MODEL}`,
      );
      activeVisionModel = FALLBACK_VISION_MODEL;
    } else if (availableModels.includes("gpt-4o")) {
      console.log(`Using fallback vision model: gpt-4o`);
      activeVisionModel = "gpt-4o";
    } else {
      console.warn(
        "⚠️ No preferred vision models are available! Will try with gpt-4.1-mini.",
      );
      activeVisionModel = "gpt-4.1-mini";
      
      // Set fallback mode flag
      usingFallbackMode = true;
    }

    return true;
  } catch (error: any) {
    console.error("❌ Error validating OpenAI API key:", error.message);

    if (error.status === 401) {
      if (isProjectBasedKey) {
        console.error(`
        =======================================================
        AUTHENTICATION ERROR: Your project-based OpenAI API key (sk-proj-*) is invalid or doesn't have proper permissions.
        
        Project-based keys often have limited permissions. You may need to:
        1. Enable the required models in your OpenAI project settings
        2. Ensure the key has access to the Chat Completions API
        3. Consider using a standard API key (sk-*) instead
        =======================================================
        `);
      } else {
        console.error(`
        =======================================================
        AUTHENTICATION ERROR: Your OpenAI API key is invalid or expired.
        Please check it at https://platform.openai.com/account/api-keys
        =======================================================
        `);
      }
    } else if (error.status === 403) {
      console.error(`
      =======================================================
      PERMISSION ERROR: Your OpenAI API key is valid but doesn't have permission to access the required features.
      Make sure your account has proper permissions for the models being used.
      =======================================================
      `);
    }

    return false;
  }
}

// Run the verification but don't block startup
(async () => {
  try {
    const isValid = await verifyApiKey();
    if (!isValid) {
      console.warn(`
      =======================================================
      WARNING: The application will continue running, but OpenAI features will use fallback content.
      The uploaded files will still be processed and saved correctly.
      =======================================================
      `);
      // Enable fallback mode for the application
      usingFallbackMode = true;
      activeVisionModel = "gpt-4.1-mini"; // Use the specified model
    }
  } catch (err) {
    console.error("Error during API key verification:", err);
  }
})();

// Response schema for story generation
const storyResponseSchema = z.object({
  english: z.string(),
  thai: z.string().optional(),
});

type StoryResponse = z.infer<typeof storyResponseSchema>;

// Common system prompts
const STORY_GENERATION_PROMPT = `
You are an expert social media storyteller for TikTok or Twitter who creates engaging captions from visual content.

Analyze the provided image(s) or video frames carefully. Pay attention to:
- The scene, setting, and subjects
- Emotions, mood, and atmosphere
- Actions, interactions, and movement
- Colors, lighting, and visual elements
- Cultural or contextual elements 

Return ONLY a JSON object with these fields:
- english: A vivid, engaging caption (50-75 words) that captures the essence of the visual content
- thai: The caption translated to Thai (optional)

Your caption should use sensory language, convey emotion, hint at a broader story, and be suitable for social media.
Never mention AI, this prompt, or formatting in your response.
`;

/**
 * Generates a story from an image using OpenAI's vision model
 */
export async function generateStoryFromImage(
  base64Image: string,
): Promise<StoryResponse> {
  // Check if we're in fallback mode due to API key issues
  if (usingFallbackMode) {
    console.log("Using fallback response due to API key limitations");
    return {
      english: "A captivating image that tells a unique visual story. The composition draws the viewer in with its distinctive elements and emotional resonance.",
      thai: "ภาพที่น่าหลงใหลซึ่งเล่าเรื่องราวที่เป็นเอกลักษณ์ องค์ประกอบของภาพดึงดูดผู้ชมด้วยความโดดเด่นและความสะเทือนใจ"
    };
  }

  try {
    console.log("Attempting to generate story from image using OpenAI API...");

    const response = await openai.chat.completions.create({
      model: activeVisionModel,
      messages: [
        {
          role: "system",
          content: STORY_GENERATION_PROMPT,
        },
        {
          role: "user",
          content: [
            {
              type: "text",
              text: "Create an engaging caption for this image that captures its essence and tells its story.",
            },
            {
              type: "image_url",
              image_url: {
                url: `data:image/jpeg;base64,${base64Image}`,
              },
            },
          ],
        },
      ],
      max_tokens: 1024,
    });

    const content = response.choices[0]?.message?.content;

    if (!content) {
      throw new Error("No content returned from OpenAI");
    }

    try {
      // Handle responses wrapped in code blocks (```json {...} ```)
      let jsonContent = content;

      // First, try to extract JSON from markdown code blocks if present
      const codeBlockMatch = content.match(
        /```(?:json)?\s*(\{[\s\S]*\})\s*```/,
      );
      if (codeBlockMatch && codeBlockMatch[1]) {
        jsonContent = codeBlockMatch[1];
        console.log("Extracted JSON from code block");
      }

      // Remove any remaining backticks or 'json' strings at the beginning
      jsonContent = jsonContent
        .replace(/^```json\s*/, "")
        .replace(/^```\s*/, "")
        .replace(/\s*```$/, "");

      // Parse the cleaned JSON content
      const parsedContent = JSON.parse(jsonContent);
      return storyResponseSchema.parse(parsedContent);
    } catch (parseError) {
      console.error("Error parsing OpenAI response:", parseError);
      console.error("Raw response content:", content);

      // Fall back to a simple response
      return {
        english: "We couldn't properly analyze this image.",
        thai: "เราไม่สามารถวิเคราะห์ภาพนี้ได้อย่างถูกต้อง",
      };
    }
  } catch (error: any) {
    console.error("Error generating story:", error);

    // Check for authentication errors
    if (error.status === 401) {
      console.error(
        "API KEY AUTHENTICATION ERROR: Please check your OpenAI API key configuration",
      );
    }

    // Check for model errors
    if (error.code === "model_not_found") {
      console.error(
        `MODEL NOT FOUND: The model '${activeVisionModel}' was not found. Check if your API key has access to this model.`,
      );
    }

    return {
      english:
        "We couldn't analyze this image. Our image analysis service is currently unavailable.",
      thai: "เราไม่สามารถวิเคราะห์ภาพนี้ได้ บริการวิเคราะห์ภาพของเราไม่พร้อมใช้งานในขณะนี้",
    };
  }
}

/**
 * Generates a story from multiple images using OpenAI's vision model
 */
export async function generateStoryFromMultipleImages(
  base64Images: string[],
): Promise<StoryResponse> {
  // Check if we're in fallback mode due to API key issues
  if (usingFallbackMode) {
    console.log("Using fallback response due to API key limitations (multiple images)");
    return {
      english: "A compelling visual narrative unfolds across these images. Each frame contributes to a unified story, creating an emotional journey through connected visual elements.",
      thai: "เรื่องราวที่น่าสนใจปรากฏขึ้นในภาพเหล่านี้ แต่ละภาพมีส่วนร่วมในการสร้างเรื่องราวที่เป็นหนึ่งเดียว สร้างการเดินทางทางอารมณ์ผ่านองค์ประกอบภาพที่เชื่อมโยงกัน"
    };
  }

  try {
    console.log("Attempting to generate story from multiple images...");

    // Build content array with all images
    const userContent: any[] = [
      {
        type: "text",
        text: "Create an engaging caption that connects these images and tells their collective story.",
      },
    ];

    // Add each image
    for (const base64Image of base64Images) {
      userContent.push({
        type: "image_url",
        image_url: {
          url: `data:image/jpeg;base64,${base64Image}`,
        },
      });
    }

    const response = await openai.chat.completions.create({
      model: activeVisionModel,
      messages: [
        {
          role: "system",
          content: STORY_GENERATION_PROMPT,
        },
        {
          role: "user",
          content: userContent,
        },
      ],
      max_tokens: 1024,
    });

    const content = response.choices[0]?.message?.content;

    if (!content) {
      throw new Error("No content returned from OpenAI");
    }

    try {
      // Handle responses wrapped in code blocks (```json {...} ```)
      let jsonContent = content;

      // First, try to extract JSON from markdown code blocks if present
      const codeBlockMatch = content.match(
        /```(?:json)?\s*(\{[\s\S]*\})\s*```/,
      );
      if (codeBlockMatch && codeBlockMatch[1]) {
        jsonContent = codeBlockMatch[1];
        console.log("Extracted JSON from code block");
      }

      // Remove any remaining backticks or 'json' strings at the beginning
      jsonContent = jsonContent
        .replace(/^```json\s*/, "")
        .replace(/^```\s*/, "")
        .replace(/\s*```$/, "");

      // Parse the cleaned JSON content
      const parsedContent = JSON.parse(jsonContent);
      return storyResponseSchema.parse(parsedContent);
    } catch (parseError) {
      console.error("Error parsing OpenAI response:", parseError);
      console.error("Raw response content:", content);

      // Fall back to a simple response
      return {
        english: "We couldn't properly analyze these images together.",
        thai: "เราไม่สามารถวิเคราะห์ภาพเหล่านี้ร่วมกันได้อย่างถูกต้อง",
      };
    }
  } catch (error: any) {
    console.error("Error generating multi-image story:", error);
    return {
      english:
        "We couldn't analyze these images together. Please try again with clearer images.",
      thai: "เราไม่สามารถวิเคราะห์ภาพเหล่านี้ร่วมกันได้ โปรดลองอีกครั้งด้วยภาพที่ชัดเจนกว่านี้",
    };
  }
}

/**
 * Generates a story from a video's extracted frames and transcript
 */
export async function generateStoryFromVideoFrames(
  framePaths: string[],
  transcript: string,
): Promise<StoryResponse> {
  // Check if we're in fallback mode due to API key issues
  if (usingFallbackMode) {
    console.log("Using fallback response due to API key limitations (video frames)");
    return {
      english: "A dynamic video sequence that captures motion and time. The visual elements tell a story of movement and action that unfolds through each frame.",
      thai: "ลำดับวิดีโอที่มีชีวิตชีวาที่จับการเคลื่อนไหวและเวลา องค์ประกอบภาพเล่าเรื่องราวของการเคลื่อนไหวและการกระทำที่คลี่คลายไปในแต่ละเฟรม"
    };
  }

  try {
    console.log("Attempting to generate story from video frames...");

    // Convert frames to base64 (limit to 10 frames as per requirements)
    const base64Frames: string[] = [];

    // If we have more than 10 frames, select 10 evenly distributed frames
    let selectedFrames: string[] = [];
    if (framePaths.length <= 10) {
      selectedFrames = framePaths;
    } else {
      // Calculate the step size to extract 10 evenly distributed frames
      const step = Math.floor(framePaths.length / 10);
      for (let i = 0; i < 10; i++) {
        const index = Math.min(i * step, framePaths.length - 1);
        selectedFrames.push(framePaths[index]);
      }
    }

    for (const framePath of selectedFrames) {
      const frameData = fs.readFileSync(framePath);
      base64Frames.push(frameData.toString("base64"));
    }

    // Build content array with text prompt and frames
    const userContent: any[] = [
      {
        type: "text",
        text: transcript
          ? `Create an engaging caption for this video based on these frames and transcript: "${transcript}".`
          : "Create an engaging caption for this video based on these frames.",
      },
    ];

    // Add each frame
    for (const base64Frame of base64Frames) {
      userContent.push({
        type: "image_url",
        image_url: {
          url: `data:image/jpeg;base64,${base64Frame}`,
        },
      });
    }

    const response = await openai.chat.completions.create({
      model: activeVisionModel,
      messages: [
        {
          role: "system",
          content: STORY_GENERATION_PROMPT,
        },
        {
          role: "user",
          content: userContent,
        },
      ],
      max_tokens: 1024,
    });

    const content = response.choices[0]?.message?.content;

    if (!content) {
      throw new Error("No content returned from OpenAI");
    }

    try {
      // Handle responses wrapped in code blocks (```json {...} ```)
      let jsonContent = content;

      // First, try to extract JSON from markdown code blocks if present
      const codeBlockMatch = content.match(
        /```(?:json)?\s*(\{[\s\S]*\})\s*```/,
      );
      if (codeBlockMatch && codeBlockMatch[1]) {
        jsonContent = codeBlockMatch[1];
        console.log("Extracted JSON from code block");
      }

      // Remove any remaining backticks or 'json' strings at the beginning
      jsonContent = jsonContent
        .replace(/^```json\s*/, "")
        .replace(/^```\s*/, "")
        .replace(/\s*```$/, "");

      // Parse the cleaned JSON content
      const parsedContent = JSON.parse(jsonContent);
      return storyResponseSchema.parse(parsedContent);
    } catch (parseError) {
      console.error("Error parsing OpenAI response:", parseError);
      console.error("Raw response content:", content);

      // Fall back to a simple response
      return {
        english: "We couldn't properly analyze this video.",
        thai: "เราไม่สามารถวิเคราะห์วิดีโอนี้ได้อย่างถูกต้อง",
      };
    }
  } catch (error: any) {
    console.error("Error generating video frame story:", error.message);
    return {
      english:
        "We couldn't analyze this video completely. You can watch it to experience the full content.",
      thai: "เราไม่สามารถวิเคราะห์วิดีโอนี้ได้อย่างสมบูรณ์ คุณสามารถดูวิดีโอเพื่อสัมผัสเนื้อหาทั้งหมด",
    };
  }
}

/**
 * Generates a story from a video thumbnail and metadata
 */
export async function generateStoryFromVideo(videoDetails: {
  filename: string;
  duration?: string;
  mimetype: string;
  size: number;
  thumbnailBase64?: string;
}): Promise<StoryResponse> {
  // Check if we're in fallback mode due to API key issues
  if (usingFallbackMode) {
    console.log("Using fallback response due to API key limitations (video metadata)");
    const duration = videoDetails.duration || "a few moments";
    return {
      english: `A ${duration} video that captures moments in time. This ${videoDetails.mimetype.split('/')[1]} format clip invites you to watch and experience the content directly.`,
      thai: `วิดีโอความยาว ${duration} ที่จับภาพช่วงเวลาต่างๆ คลิปรูปแบบ ${videoDetails.mimetype.split('/')[1]} นี้เชิญชวนให้คุณรับชมและสัมผัสประสบการณ์เนื้อหาโดยตรง`
    };
  }

  try {
    console.log("Generating story from video details...");

    // Build content array
    const userContent: any[] = [
      {
        type: "text",
        text: `Create an engaging caption for a video with these details:
- Filename: ${videoDetails.filename}
- Duration: ${videoDetails.duration || "Unknown"}
- Format: ${videoDetails.mimetype}
- Size: ${Math.round((videoDetails.size / 1024 / 1024) * 10) / 10}MB`,
      },
    ];

    // Add thumbnail if available
    if (videoDetails.thumbnailBase64) {
      userContent.push({
        type: "image_url",
        image_url: {
          url: `data:image/jpeg;base64,${videoDetails.thumbnailBase64}`,
        },
      });
    }

    const response = await openai.chat.completions.create({
      model: activeVisionModel,
      messages: [
        {
          role: "system",
          content: STORY_GENERATION_PROMPT,
        },
        {
          role: "user",
          content: userContent,
        },
      ],
      max_tokens: 1024,
    });

    const content = response.choices[0]?.message?.content;

    if (!content) {
      throw new Error("No content returned from OpenAI");
    }

    try {
      // Handle responses wrapped in code blocks (```json {...} ```)
      let jsonContent = content;

      // First, try to extract JSON from markdown code blocks if present
      const codeBlockMatch = content.match(
        /```(?:json)?\s*(\{[\s\S]*\})\s*```/,
      );
      if (codeBlockMatch && codeBlockMatch[1]) {
        jsonContent = codeBlockMatch[1];
        console.log("Extracted JSON from code block");
      }

      // Remove any remaining backticks or 'json' strings at the beginning
      jsonContent = jsonContent
        .replace(/^```json\s*/, "")
        .replace(/^```\s*/, "")
        .replace(/\s*```$/, "");

      // Parse the cleaned JSON content
      const parsedContent = JSON.parse(jsonContent);
      return storyResponseSchema.parse(parsedContent);
    } catch (parseError) {
      console.error("Error parsing OpenAI response:", parseError);
      console.error("Raw response content:", content);

      // Fall back to a simple response
      return {
        english:
          "We've processed your video. Watch it to experience the full story.",
        thai: "เราได้ประมวลผลวิดีโอของคุณแล้ว ดูวิดีโอเพื่อสัมผัสเรื่องราวทั้งหมด",
      };
    }
  } catch (error: any) {
    console.error("Error generating video story:", error.message);
    return {
      english:
        "We've processed your video. Watch it to experience the full story.",
      thai: "เราได้ประมวลผลวิดีโอของคุณแล้ว ดูวิดีโอเพื่อสัมผัสเรื่องราวทั้งหมด",
    };
  }
}
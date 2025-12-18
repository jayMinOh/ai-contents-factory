import axios from "axios";

const api = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
  timeout: 120000, // 2 minutes for long AI operations
});

export interface AnalyzeRequest {
  url: string;
  extract_audio?: boolean;
}

export interface TimelineSegment {
  start_time: number;
  end_time: number;
  segment_type: string;
  visual_description: string;
  audio_transcript?: string;
  text_overlay?: string;
  engagement_score: number;
  techniques: string[];
}

export interface HookPoint {
  timestamp: string;
  hook_type: string;
  effectiveness_score: number;
  description?: string;
  elements?: string[];
  adaptable_template?: string;
}

export interface EdgePoint {
  category: string;
  description: string;
  impact_score: number;
  how_to_apply: string;
}

export interface EmotionalTrigger {
  timestamp: string;
  trigger_type: string;
  intensity: number;
  description: string;
}

export interface PainPoint {
  timestamp: string;
  pain_type: string;
  description: string;
  empathy_technique: string;
}

export interface ApplicationPoint {
  type: string;
  content: string;
  context: string;
}

export interface SellingPoint {
  timestamp: string;
  claim: string;
  evidence_type: string;
  persuasion_technique: string;
  effectiveness?: number;
}

export interface CTAAnalysis {
  cta_type: string;
  placement: string;
  urgency_elements: string[];
  barrier_removal: string[];
  effectiveness_score: number;
}

export interface StructurePattern {
  framework: string;
  flow: string[];
  effectiveness_note: string;
}

export interface Recommendation {
  priority: number;
  action: string;
  reason: string;
  example: string;
}

export interface AnalysisResult {
  analysis_id: string;
  source_url: string;
  title: string;
  status: string;
  duration?: number;
  tags?: string[];
  notes?: string;
  error_message?: string;
  segments: TimelineSegment[];
  hook_points: HookPoint[];
  edge_points: EdgePoint[];
  emotional_triggers: EmotionalTrigger[];
  pain_points: PainPoint[];
  application_points: ApplicationPoint[];
  selling_points: SellingPoint[];
  cta_analysis?: CTAAnalysis;
  structure_pattern?: StructurePattern | string;
  recommendations: Recommendation[] | string[];
  transcript?: string;
}

export const referenceApi = {
  analyze: async (data: AnalyzeRequest) => {
    const response = await api.post("/references/analyze", data);
    return response.data;
  },

  getAnalysis: async (analysisId: string): Promise<AnalysisResult> => {
    const response = await api.get(`/references/${analysisId}`);
    return response.data;
  },

  listAnalyses: async (): Promise<AnalysisResult[]> => {
    const response = await api.get("/references/");
    return response.data;
  },
};

// ========== Brand & Product Types ==========

// Cosmetics-specific type definitions
export type ProductCategory =
  | "serum" | "cream" | "toner" | "essence" | "oil" | "mask"
  | "cleanser" | "sunscreen" | "moisturizer" | "eye_care" | "lip_care"
  | "mist" | "ampoule" | "lotion" | "emulsion" | "balm" | "gel"
  | "foam" | "shampoo" | "conditioner" | "treatment" | "other";

export type SkinType = "dry" | "oily" | "combination" | "normal" | "sensitive" | "all";

export type SkinConcern =
  | "acne" | "pores" | "wrinkles" | "fine_lines" | "dark_spots"
  | "pigmentation" | "dullness" | "redness" | "dryness" | "oiliness"
  | "sagging" | "elasticity" | "uneven_tone" | "dark_circles" | "sensitivity"
  | "dehydration" | "blackheads" | "whiteheads" | "aging" | "sun_damage"
  | "texture" | "barrier_damage" | "hair_loss" | "dandruff" | "scalp_trouble" | "other";

export type IngredientCategory =
  | "active" | "moisturizing" | "soothing" | "antioxidant" | "exfoliant"
  | "brightening" | "firming" | "barrier" | "anti_aging" | "hydrating"
  | "cleansing" | "other";

export type TextureType =
  | "cream" | "gel" | "serum" | "oil" | "water" | "milk" | "balm"
  | "foam" | "mousse" | "mist" | "powder" | "stick" | "sheet" | "patch" | "other";

export type FinishType =
  | "matte" | "dewy" | "satin" | "natural" | "luminous" | "velvet" | "glossy" | "invisible";

export interface Ingredient {
  name: string;
  name_ko?: string;
  effect: string;
  category?: IngredientCategory;
  concentration?: string;
  is_hero?: boolean;
}

export interface Product {
  id: string;
  brand_id: string;
  name: string;
  description?: string;
  // Product Image
  image_url?: string;
  image_description?: string;
  features: string[];
  benefits: string[];
  price_range?: string;
  target_segment?: string;
  // Cosmetics-specific fields
  product_category?: ProductCategory;
  key_ingredients: Ingredient[];
  suitable_skin_types: SkinType[];
  skin_concerns: SkinConcern[];
  texture_type?: TextureType;
  finish_type?: FinishType;
  volume_ml?: number;
  created_at: string;
  updated_at: string;
}

export interface ProductCreate {
  name: string;
  description?: string;
  features?: string[];
  benefits?: string[];
  price_range?: string;
  target_segment?: string;
  // Cosmetics-specific fields
  product_category?: ProductCategory;
  key_ingredients?: Ingredient[];
  suitable_skin_types?: SkinType[];
  skin_concerns?: SkinConcern[];
  texture_type?: TextureType;
  finish_type?: FinishType;
  volume_ml?: number;
}

export interface ProductUpdate {
  name?: string;
  description?: string;
  features?: string[];
  benefits?: string[];
  price_range?: string;
  target_segment?: string;
  // Cosmetics-specific fields
  product_category?: ProductCategory;
  key_ingredients?: Ingredient[];
  suitable_skin_types?: SkinType[];
  skin_concerns?: SkinConcern[];
  texture_type?: TextureType;
  finish_type?: FinishType;
  volume_ml?: number;
}

export interface Brand {
  id: string;
  name: string;
  description?: string;
  logo_url?: string;
  target_audience?: string;
  tone_and_manner?: string;
  usp?: string;
  keywords: string[];
  industry?: string;
  created_at: string;
  updated_at: string;
  products: Product[];
}

export interface BrandSummary {
  id: string;
  name: string;
  description?: string;
  logo_url?: string;
  target_audience?: string;
  tone_and_manner?: string;
  usp?: string;
  keywords: string[];
  industry?: string;
  created_at: string;
  updated_at: string;
  product_count: number;
}

export interface BrandCreate {
  name: string;
  description?: string;
  logo_url?: string;
  target_audience?: string;
  tone_and_manner?: string;
  usp?: string;
  keywords?: string[];
  industry?: string;
}

export interface BrandUpdate {
  name?: string;
  description?: string;
  logo_url?: string;
  target_audience?: string;
  tone_and_manner?: string;
  usp?: string;
  keywords?: string[];
  industry?: string;
}

// ========== Brand API ==========

// ========== Video Studio Types ==========

export interface VideoProject {
  id: string;
  title: string;
  description?: string;
  brand_id: string;
  product_id: string;
  reference_analysis_id?: string;
  status: string;
  current_step: number;
  script?: Record<string, unknown>;
  storyboard?: Record<string, unknown>;
  target_duration?: number;
  aspect_ratio: string;
  video_provider?: string;
  image_provider?: string;
  output_video_url?: string;
  output_thumbnail_url?: string;
  output_duration?: number;
  error_message?: string;
  scene_images: SceneImage[];
  created_at: string;
  updated_at: string;
  completed_at?: string;
}

export interface VideoProjectSummary {
  id: string;
  title: string;
  status: string;
  current_step: number;
  brand_id: string;
  product_id: string;
  output_thumbnail_url?: string;
  created_at: string;
  updated_at: string;
}

export interface VideoProjectCreate {
  title: string;
  description?: string;
  brand_id: string;
  product_id: string;
  reference_analysis_id?: string;
  target_duration?: number;
  aspect_ratio?: string;
}

export interface VideoProjectUpdate {
  title?: string;
  description?: string;
  current_step?: number;
  script?: Record<string, unknown>;
  storyboard?: Record<string, unknown>;
  target_duration?: number;
  aspect_ratio?: string;
  video_provider?: string;
  image_provider?: string;
}

export interface SceneImage {
  id: string;
  scene_number: number;
  source: "uploaded" | "ai_generated";
  image_url: string;
  thumbnail_url?: string;
  scene_segment_type?: string;
  scene_description?: string;
  duration_seconds?: number;
  version: number;
  is_active: boolean;
  created_at: string;
}

export interface SceneImageGenerate {
  scene_number: number;
  prompt?: string;
  scene_segment_type?: string;
  scene_description?: string;
  duration_seconds?: number;
  provider?: string;
}

// Temporary image response (before saving to DB)
export interface TempImageResponse {
  temp_id: string;
  filename: string;
  preview_url: string;
  mime_type: string;
  generation_time_ms?: number;
  generation_provider?: string;
  generation_prompt?: string;
  scene_number?: number;
  scene_description?: string;
  scene_segment_type?: string;
  duration_seconds?: number;
}

export interface SaveSceneImageRequest {
  scene_number: number;
  temp_id: string;
  filename: string;
  source: "uploaded" | "ai_generated";
  scene_segment_type?: string;
  scene_description?: string;
  duration_seconds?: number;
  generation_prompt?: string;
  generation_provider?: string;
  generation_duration_ms?: number;
}

// ========== Storyboard Types ==========

export interface Scene {
  scene_number: number;
  scene_type: string;
  title: string;
  description: string;
  narration_script?: string;
  visual_direction?: string;
  background_music_suggestion?: string;
  transition_effect?: string;
  subtitle_text?: string;
  duration_seconds: number;
  generated_image_id?: string;
}

export interface Storyboard {
  id: string;
  video_project_id: string;
  generation_mode: "reference_structure" | "ai_optimized";
  source_reference_analysis_id?: string;
  scenes: Scene[];
  total_duration_seconds?: number;
  version: number;
  is_active: boolean;
  previous_version_id?: string;
  created_at: string;
  updated_at: string;
}

export interface StoryboardGenerateRequest {
  mode: "reference_structure" | "ai_optimized";
  // Creative input (Step 3)
  concept?: string;
  target_duration?: number;
  mood?: string;
  style?: string;
  additional_notes?: string;
  // Selected reference points (Step 2)
  reference_points?: {
    use_structure: boolean;
    use_flow: boolean;
    use_cta_style: boolean;
    selected_hook_indices: number[];
    selected_segment_indices: number[];
    selected_selling_indices: number[];
  };
  // Reference images
  reference_image_ids?: string[];
}

export interface SceneUpdateRequest {
  title?: string;
  description?: string;
  narration_script?: string;
  visual_direction?: string;
  background_music_suggestion?: string;
  transition_effect?: string;
  subtitle_text?: string;
  duration_seconds?: number;
}

export interface SceneCreateRequest {
  scene_type: string;
  title: string;
  description: string;
  insert_after?: number;
  narration_script?: string;
  visual_direction?: string;
  background_music_suggestion?: string;
  transition_effect?: string;
  subtitle_text?: string;
  duration_seconds?: number;
}

export interface VideoGenerationStatus {
  status: "pending" | "processing" | "completed" | "failed";
  video_url?: string;
  operation_id?: string;
  error_message?: string;
  generation_time_ms?: number;
}

// Per-scene video generation status
export interface SceneVideoStatus {
  scene_number: number;
  status: "pending" | "processing" | "completed" | "failed";
  video_url?: string;
  thumbnail_url?: string;
  duration_seconds?: number;
  operation_id?: string;
  error_message?: string;
  scene_segment_type?: string;
}

// Extended video generation status with per-scene support
export interface ExtendedVideoGenerationStatus {
  status: "pending" | "processing" | "completed" | "failed";
  video_url?: string;
  operation_id?: string;
  error_message?: string;
  generation_time_ms?: number;
  scene_videos?: SceneVideoStatus[];
  concatenation_status?: "pending" | "processing" | "completed" | "failed";
  final_video_url?: string;
}

// Scene Extension video generation response
export interface ExtendedVideoGenerationResponse {
  status: "processing" | "completed" | "failed";
  video_url?: string;
  initial_duration_seconds?: number;
  final_duration_seconds?: number;
  extension_hops_completed: number;
  scenes_processed: number;
  generation_time_ms?: number;
  error_message?: string;
  operation_id?: string;
}

// ========== Studio API ==========

export const studioApi = {
  // Project CRUD
  createProject: async (data: VideoProjectCreate): Promise<VideoProject> => {
    const response = await api.post("/studio/projects/", data);
    return response.data;
  },

  listProjects: async (brandId?: string, status?: string): Promise<VideoProjectSummary[]> => {
    const params = new URLSearchParams();
    if (brandId) params.append("brand_id", brandId);
    if (status) params.append("status", status);
    const response = await api.get(`/studio/projects/?${params}`);
    return response.data;
  },

  getProject: async (projectId: string): Promise<VideoProject> => {
    const response = await api.get(`/studio/projects/${projectId}`);
    return response.data;
  },

  updateProject: async (projectId: string, data: VideoProjectUpdate): Promise<VideoProject> => {
    const response = await api.patch(`/studio/projects/${projectId}`, data);
    return response.data;
  },

  deleteProject: async (projectId: string): Promise<void> => {
    await api.delete(`/studio/projects/${projectId}`);
  },

  // Scene Images - Temporary upload (for preview, NOT saved to DB)
  uploadTempImage: async (
    projectId: string,
    file: File
  ): Promise<TempImageResponse> => {
    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post(
      `/studio/projects/${projectId}/scenes/upload-temp`,
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return response.data;
  },

  // AI Image Generation (for preview, NOT saved to DB)
  generateSceneImage: async (projectId: string, data: SceneImageGenerate): Promise<TempImageResponse> => {
    const response = await api.post(`/studio/projects/${projectId}/scenes/generate`, data);
    return response.data;
  },

  // Save temporary image to permanent storage and DB
  saveSceneImage: async (projectId: string, data: SaveSceneImageRequest): Promise<SceneImage> => {
    const params = new URLSearchParams();
    params.append("scene_number", data.scene_number.toString());
    params.append("temp_id", data.temp_id);
    params.append("filename", data.filename);
    params.append("source", data.source);
    if (data.scene_segment_type) params.append("scene_segment_type", data.scene_segment_type);
    if (data.scene_description) params.append("scene_description", data.scene_description);
    if (data.duration_seconds) params.append("duration_seconds", data.duration_seconds.toString());
    if (data.generation_prompt) params.append("generation_prompt", data.generation_prompt);
    if (data.generation_provider) params.append("generation_provider", data.generation_provider);
    if (data.generation_duration_ms) params.append("generation_duration_ms", data.generation_duration_ms.toString());

    const response = await api.post(`/studio/projects/${projectId}/scenes/save?${params}`);
    return response.data;
  },

  listSceneImages: async (projectId: string, activeOnly: boolean = true): Promise<SceneImage[]> => {
    const response = await api.get(`/studio/projects/${projectId}/scenes/?active_only=${activeOnly}`);
    return response.data;
  },

  deleteSceneImage: async (projectId: string, sceneId: string): Promise<void> => {
    await api.delete(`/studio/projects/${projectId}/scenes/${sceneId}`);
  },

  // Storyboard
  generateStoryboard: async (projectId: string, data: StoryboardGenerateRequest): Promise<Storyboard> => {
    // Get browser language for localized storyboard content
    const browserLang = typeof navigator !== 'undefined' ? navigator.language : 'ko';
    const response = await api.post(`/studio/projects/${projectId}/storyboard/generate`, data, {
      headers: {
        "Accept-Language": browserLang,
      },
    });
    return response.data;
  },

  getStoryboard: async (projectId: string): Promise<Storyboard> => {
    const response = await api.get(`/studio/projects/${projectId}/storyboard`);
    return response.data;
  },

  getStoryboardVersions: async (projectId: string): Promise<Storyboard[]> => {
    const response = await api.get(`/studio/projects/${projectId}/storyboard/versions`);
    return response.data;
  },

  updateScene: async (projectId: string, sceneNumber: number, data: SceneUpdateRequest): Promise<Storyboard> => {
    const response = await api.put(`/studio/projects/${projectId}/storyboard/scenes/${sceneNumber}`, data);
    return response.data;
  },

  addScene: async (projectId: string, data: SceneCreateRequest): Promise<Storyboard> => {
    const response = await api.post(`/studio/projects/${projectId}/storyboard/scenes`, data);
    return response.data;
  },

  deleteScene: async (projectId: string, sceneNumber: number): Promise<Storyboard> => {
    const response = await api.delete(`/studio/projects/${projectId}/storyboard/scenes/${sceneNumber}`);
    return response.data;
  },

  reorderScenes: async (projectId: string, sceneOrder: number[]): Promise<Storyboard> => {
    const response = await api.put(`/studio/projects/${projectId}/storyboard/scenes/reorder`, { scene_order: sceneOrder });
    return response.data;
  },

  // Marketing Image Production (New)
  analyzeMarketingImage: async (formData: FormData): Promise<{
    temp_id: string;
    filename: string;
    preview_url: string;
    description: string;
    detected_type: string;
    is_realistic: boolean;  // true: photo/realistic, false: illustration/animation
    elements: string[];
    visual_prompt: string;  // Detailed visual description for AI generation
  }> => {
    // Get browser language for localized analysis
    const browserLang = typeof navigator !== 'undefined' ? navigator.language : 'en';
    const response = await api.post("/studio/images/analyze", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
        "Accept-Language": browserLang,
      },
    });
    return response.data;
  },

  generateMarketingImage: async (data: {
    images: Array<{
      temp_url: string;
      analysis?: {
        description: string;
        detected_type: string;
        elements: string[];
        visual_prompt?: string;
      };
    }>;
    prompt: string;
    aspect_ratio?: string;
  }): Promise<{
    image_id: string;
    image_url: string;
    generation_time_ms?: number;
    optimized_prompt: string;
  }> => {
    const response = await api.post("/studio/images/generate", data);
    return response.data;
  },

  /**
   * Edit/generate an image while preserving the exact appearance of the product.
   * Uses Gemini's multimodal capabilities to place the product in new contexts.
   *
   * Example prompts:
   * - "A woman holding this product in a bathroom setting"
   * - "This product on a marble countertop with soft lighting"
   */
  editImageWithProduct: async (data: {
    product_image_temp_id?: string;  // Legacy single image
    image_temp_ids?: string[];  // New: all images to use
    prompt: string;
    aspect_ratio?: string;
    product_description?: string;
    background_image_temp_id?: string;
  }): Promise<{
    image_id: string;
    image_url: string;
    generation_time_ms?: number;
    mime_type: string;
  }> => {
    const response = await api.post("/studio/images/edit-with-product", data);
    return response.data;
  },

  /**
   * Compose a marketing scene with a product placed on a background.
   * More advanced composition with optional custom backgrounds.
   */
  composeSceneWithProduct: async (data: {
    product_image_temp_id: string;
    scene_prompt: string;
    background_image_temp_id?: string;
    aspect_ratio?: string;
    product_description?: string;
  }): Promise<{
    image_id: string;
    image_url: string;
    generation_time_ms?: number;
    mime_type: string;
  }> => {
    const response = await api.post("/studio/images/compose-scene", data);
    return response.data;
  },

  // Video Generation
  generateVideo: async (
    projectId: string,
    data: {
      provider?: string;  // "veo" or "mock"
      aspect_ratio?: string;  // "16:9", "9:16", "1:1"
    }
  ): Promise<VideoGenerationStatus> => {
    const response = await api.post(`/studio/projects/${projectId}/video/generate`, data);
    return response.data;
  },

  getVideoStatus: async (
    projectId: string,
    operationId?: string
  ): Promise<VideoGenerationStatus> => {
    const params = operationId ? `?operation_id=${operationId}` : "";
    const response = await api.get(`/studio/projects/${projectId}/video/status${params}`);
    return response.data;
  },

  generateVideoPreview: async (
    projectId: string,
    sceneNumber: number,
    data: {
      provider?: string;
      aspect_ratio?: string;
    }
  ): Promise<VideoGenerationStatus> => {
    const response = await api.post(
      `/studio/projects/${projectId}/video/generate-preview?scene_number=${sceneNumber}`,
      data
    );
    return response.data;
  },

  // Per-scene video generation (new endpoint)
  generateSceneVideo: async (
    projectId: string,
    sceneNumber: number,
    data: {
      provider?: string;
      aspect_ratio?: string;
    }
  ): Promise<SceneVideoStatus> => {
    const response = await api.post(
      `/studio/projects/${projectId}/video/generate-scene`,
      { scene_number: sceneNumber, ...data }
    );
    return response.data;
  },

  // Concatenate all scene videos into final video
  concatenateVideos: async (
    projectId: string,
    data?: {
      transition_type?: string;
      include_audio?: boolean;
    }
  ): Promise<ExtendedVideoGenerationStatus> => {
    const response = await api.post(
      `/studio/projects/${projectId}/video/concatenate`,
      data || {}
    );
    return response.data;
  },

  // Get scene video status
  getSceneVideoStatus: async (
    projectId: string,
    sceneNumber: number
  ): Promise<SceneVideoStatus> => {
    const response = await api.get(
      `/studio/projects/${projectId}/video/scene-status?scene_number=${sceneNumber}`
    );
    return response.data;
  },

  // Get all scene videos status
  getAllSceneVideosStatus: async (
    projectId: string
  ): Promise<SceneVideoStatus[]> => {
    const response = await api.get(
      `/studio/projects/${projectId}/video/scenes-status`
    );
    return response.data;
  },

  // Scene Extension video generation - generates entire video using scene extension
  generateExtendedVideo: async (
    projectId: string,
    data?: {
      target_duration_seconds?: number;
      aspect_ratio?: string;
      provider?: string;
    }
  ): Promise<ExtendedVideoGenerationResponse> => {
    const response = await api.post(
      `/studio/projects/${projectId}/video/generate-extended`,
      data || {},
      { timeout: 600000 } // 10 minutes for long video generation
    );
    return response.data;
  },

  // Get extended video generation status
  getExtendedVideoStatus: async (
    projectId: string,
    operationId?: string
  ): Promise<ExtendedVideoGenerationResponse> => {
    const params = operationId ? `?operation_id=${operationId}` : "";
    const response = await api.get(
      `/studio/projects/${projectId}/video/extended-status${params}`
    );
    return response.data;
  },
};

export const brandApi = {
  // Brand CRUD
  create: async (data: BrandCreate): Promise<Brand> => {
    const response = await api.post("/brands/", data);
    return response.data;
  },

  list: async (): Promise<BrandSummary[]> => {
    const response = await api.get("/brands/");
    return response.data;
  },

  get: async (brandId: string): Promise<Brand> => {
    const response = await api.get(`/brands/${brandId}`);
    return response.data;
  },

  update: async (brandId: string, data: BrandUpdate): Promise<Brand> => {
    const response = await api.put(`/brands/${brandId}`, data);
    return response.data;
  },

  delete: async (brandId: string): Promise<void> => {
    await api.delete(`/brands/${brandId}`);
  },

  // Product CRUD
  createProduct: async (brandId: string, data: ProductCreate): Promise<Product> => {
    const response = await api.post(`/brands/${brandId}/products`, data);
    return response.data;
  },

  listProducts: async (brandId: string): Promise<Product[]> => {
    const response = await api.get(`/brands/${brandId}/products`);
    return response.data;
  },

  getProduct: async (brandId: string, productId: string): Promise<Product> => {
    const response = await api.get(`/brands/${brandId}/products/${productId}`);
    return response.data;
  },

  updateProduct: async (brandId: string, productId: string, data: ProductUpdate): Promise<Product> => {
    const response = await api.put(`/brands/${brandId}/products/${productId}`, data);
    return response.data;
  },

  deleteProduct: async (brandId: string, productId: string): Promise<void> => {
    await api.delete(`/brands/${brandId}/products/${productId}`);
  },

  uploadProductImage: async (brandId: string, productId: string, file: File): Promise<Product> => {
    const formData = new FormData();
    formData.append("file", file);
    const response = await api.post(
      `/brands/${brandId}/products/${productId}/image`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      }
    );
    return response.data;
  },
};

export default api;

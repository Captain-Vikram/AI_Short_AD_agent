export type Scene = {
  scene: number;
  image: string | null;
  audio: string | null;
  narration: string;
  start: number;
  duration: number;
  image_prompt?: string;
};

export type DesignSystem = {
  bg_color?: string;
  accent_color?: string;
  text_color?: string;
  secondary_color?: string;
  layout?: "fullscreen" | "split" | "picture-in-picture" | "minimalist";
  animation_style?: "subtle" | "dynamic" | "bold";
  floating_elements?: boolean;
  show_badge?: boolean;
  text_position?: "bottom" | "center" | "top";
  element_scale?: number;
  blur_strength?: number;
  audio_gain?: number;
  [key: string]: unknown;
};

export type VideoProps = {
  scenes: Scene[];
  total_duration: number;
  video?: {
    width: number;
    height: number;
    aspect_ratio?: string;
  };
  design?: DesignSystem;
};

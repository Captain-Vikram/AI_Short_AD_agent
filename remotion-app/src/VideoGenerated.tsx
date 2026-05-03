import React from "react";

import { VideoEnhanced } from "./VideoEnhanced";
import type { VideoProps } from "./types";

/**
 * VideoGenerated composition for LLM-generated or custom design specifications.
 * Uses the same enhanced template system as Video but allows for design-driven customization.
 * The design props are read from the generated video_design.json and applied here.
 */
export const VideoGenerated: React.FC<VideoProps> = (props) => <VideoEnhanced {...props} />;

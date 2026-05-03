import React from "react";
import { Composition } from "remotion";

import { Video } from "./Video";
import { VideoGenerated } from "./VideoGenerated";
import type { VideoProps } from "./types";

const fps = 30;
const defaultWidth = 1080;
const defaultHeight = 1920;

const resolveTotalDuration = (props: VideoProps): number => {
  if (!props?.scenes?.length) {
    return props?.total_duration || 1;
  }
  // Calculate the absolute end time of the last scene
  const lastSceneEnd = props.scenes.reduce((maxEnd, scene) => {
    return Math.max(maxEnd, scene.start + scene.duration);
  }, 0);
  
  // Return the larger of the calculated end or the explicit total_duration
  return Math.max(1, lastSceneEnd, props.total_duration || 0);
};

const resolveDimensions = (props: VideoProps) => {
  const width = Number(props?.video?.width);
  const height = Number(props?.video?.height);
  if (!isNaN(width) && !isNaN(height) && width > 0 && height > 0) {
    return { width, height };
  }
  return { width: defaultWidth, height: defaultHeight };
};

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="Video"
      component={Video}
      durationInFrames={fps}
      fps={fps}
      width={defaultWidth}
      height={defaultHeight}
      defaultProps={{ scenes: [], total_duration: 1 }}
      calculateMetadata={({ props }) => {
        const totalSeconds = resolveTotalDuration(props as VideoProps);
        const dimensions = resolveDimensions(props as VideoProps);
        return {
          durationInFrames: Math.max(1, Math.round(totalSeconds * fps)),
          fps,
          width: dimensions.width,
          height: dimensions.height,
          props,
        };
      }}
    />
    <Composition
      id="VideoGenerated"
      component={VideoGenerated}
      durationInFrames={fps}
      fps={fps}
      width={defaultWidth}
      height={defaultHeight}
      defaultProps={{ scenes: [], total_duration: 1 }}
      calculateMetadata={({ props }) => {
        const totalSeconds = resolveTotalDuration(props as VideoProps);
        const dimensions = resolveDimensions(props as VideoProps);
        return {
          durationInFrames: Math.max(1, Math.round(totalSeconds * fps)),
          fps,
          width: dimensions.width,
          height: dimensions.height,
          props,
        };
      }}
    />
  </>
);

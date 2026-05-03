import React from "react";
import { Composition } from "remotion";

import { Video } from "./Video";
import { VideoGenerated } from "./VideoGenerated";
import type { VideoProps } from "./types";

const fps = 30;
const defaultWidth = 1080;
const defaultHeight = 1920;

const resolveTotalDuration = (props: VideoProps): number => {
  if (props?.total_duration && props.total_duration > 0) {
    return props.total_duration;
  }
  if (!props?.scenes?.length) {
    return 1;
  }
  const last = props.scenes.reduce((acc, scene) => Math.max(acc, scene.start + scene.duration), 0);
  return Math.max(1, last);
};

const resolveDimensions = (props: VideoProps) => {
  const width = props?.video?.width;
  const height = props?.video?.height;
  if (typeof width === "number" && typeof height === "number" && width > 0 && height > 0) {
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

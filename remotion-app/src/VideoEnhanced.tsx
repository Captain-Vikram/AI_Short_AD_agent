import React from "react";
import {
  AbsoluteFill,
  Audio,
  Easing,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

import type { Scene, VideoProps } from "./types";

const secondsToFrames = (seconds: number, fps: number) => Math.round(seconds * fps);

const resolveMediaPath = (value?: string | null) => {
  if (!value) {
    return null;
  }
  const normalized = value.replace(/\\/g, "/");
  const assetIndex = normalized.indexOf("assets/");
  const relative = assetIndex >= 0 ? normalized.slice(assetIndex) : normalized;
  return staticFile(relative);
};

type DesignConfig = {
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
};

const defaultDesign: DesignConfig = {
  bg_color: "#0b0d12",
  accent_color: "#3b82f6",
  text_color: "#f8fafc",
  secondary_color: "#1e293b",
  layout: "fullscreen",
  animation_style: "dynamic",
  floating_elements: true,
  show_badge: true,
  text_position: "bottom",
  element_scale: 1,
  blur_strength: 6,
  audio_gain: 1.4,
};

const parseDesign = (design: any): DesignConfig => ({
  ...defaultDesign,
  ...(typeof design === "object" ? design : {}),
});

const FloatingElement: React.FC<{
  frame: number;
  durationFrames: number;
  index: number;
  color: string;
  size: number;
}> = ({ frame, durationFrames, index, color, size }) => {
  const offsetX = Math.sin((index + frame * 0.02) * 0.05) * 100;
  const offsetY = Math.cos((index * 2 + frame * 0.015) * 0.05) * 80;
  const scale = 0.8 + Math.sin(frame * 0.03 + index) * 0.2;
  const opacity = interpolate(
    frame,
    [0, durationFrames * 0.3, durationFrames * 0.7, durationFrames],
    [0, 0.6, 0.6, 0]
  );

  return (
    <div
      style={{
        position: "absolute",
        left: `${20 + (index % 4) * 20}%`,
        top: `${15 + (index % 3) * 25}%`,
        width: size,
        height: size,
        borderRadius: "50%",
        backgroundColor: color,
        opacity,
        transform: `translate(${offsetX}px, ${offsetY}px) scale(${scale})`,
        filter: `blur(${1 + Math.sin(frame * 0.02) * 0.5}px)`,
      }}
    />
  );
};

const ShapeAccent: React.FC<{
  frame: number;
  durationFrames: number;
  color: string;
  position: "top-left" | "top-right" | "bottom-left" | "bottom-right";
}> = ({ frame, durationFrames, color, position }) => {
  const rotation = interpolate(frame, [0, durationFrames], [0, 360], { extrapolateRight: "clamp" });
  const opacity = interpolate(
    frame,
    [0, durationFrames * 0.2, durationFrames * 0.8, durationFrames],
    [0, 0.3, 0.3, 0]
  );

  const positionStyles: Record<string, React.CSSProperties> = {
    "top-left": { top: -50, left: -50 },
    "top-right": { top: -50, right: -50 },
    "bottom-left": { bottom: -50, left: -50 },
    "bottom-right": { bottom: -50, right: -50 },
  };

  return (
    <div
      style={{
        position: "absolute",
        ...positionStyles[position],
        width: 200,
        height: 200,
        borderRadius: "20%",
        backgroundColor: color,
        opacity,
        transform: `rotate(${rotation}deg)`,
        mixBlendMode: "multiply",
      }}
    />
  );
};

const TextOverlay: React.FC<{
  text: string;
  position: "bottom" | "center" | "top";
  textColor: string;
  accentColor: string;
  badgeText?: string;
  showBadge: boolean;
}> = ({ text, position, textColor, accentColor, badgeText, showBadge }) => {
  const positionStyles: Record<string, React.CSSProperties> = {
    bottom: { bottom: 64, left: 0, right: 0 },
    center: { top: "50%", left: 0, right: 0, transform: "translateY(-50%)" },
    top: { top: 64, left: 0, right: 0 },
  };

  return (
    <div
      style={{
        position: "absolute",
        ...positionStyles[position],
        padding: "32px 40px",
        zIndex: 10,
      }}
    >
      {showBadge && badgeText && (
        <div
          style={{
            display: "inline-block",
            padding: "8px 16px",
            borderRadius: "20px",
            backgroundColor: accentColor,
            color: "#fff",
            fontSize: 12,
            fontWeight: 700,
            letterSpacing: 1,
            marginBottom: 16,
            textTransform: "uppercase",
          }}
        >
          {badgeText}
        </div>
      )}
      <div
        style={{
          fontSize: 48,
          fontWeight: 700,
          lineHeight: 1.2,
          color: textColor,
          textShadow: `0 10px 30px rgba(0,0,0,0.6)`,
          maxWidth: 800,
          wordWrap: "break-word",
        }}
      >
        {text}
      </div>
    </div>
  );
};

const ImageLayer: React.FC<{
  frame: number;
  durationFrames: number;
  imageSrc: string | null;
  accentColor: string;
  blurStrength: number;
}> = ({ frame, durationFrames, imageSrc, accentColor, blurStrength }) => {
  const scaleIn = interpolate(
    frame,
    [0, durationFrames * 0.2],
    [0.95, 1],
    {
      easing: Easing.out(Easing.cubic),
      extrapolateRight: "clamp",
    }
  );

  const fadeOut = interpolate(
    frame,
    [durationFrames * 0.8, durationFrames],
    [1, 0],
    { extrapolateLeft: "clamp" }
  );

  return (
    <AbsoluteFill
      style={{
        opacity: fadeOut,
        transform: `scale(${scaleIn})`,
        overflow: "hidden",
      }}
    >
      {imageSrc ? (
        <Img
          src={imageSrc}
          style={{
            width: "100%",
            height: "100%",
            objectFit: "cover",
            filter: `contrast(1.1) saturate(1.15) drop-shadow(0 20px 40px rgba(0,0,0,0.5))`,
          }}
        />
      ) : (
        <div
          style={{
            width: "100%",
            height: "100%",
            background: `linear-gradient(135deg, ${accentColor}22 0%, ${accentColor}44 100%)`,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontSize: 60,
            fontWeight: 700,
            color: accentColor,
            opacity: 0.3,
          }}
        >
          ∿
        </div>
      )}
    </AbsoluteFill>
  );
};

type SceneLayerProps = {
  scene: Scene;
  durationFrames: number;
  design: DesignConfig;
};

const SceneLayer: React.FC<SceneLayerProps> = ({ scene, durationFrames, design }) => {
  const frame = useCurrentFrame();
  const imageSrc = resolveMediaPath(scene.image);
  const audioSrc = resolveMediaPath(scene.audio);

  const fadeFrames = Math.max(1, Math.round(durationFrames * 0.15));
  const sceneOpacity = interpolate(
    frame,
    [0, fadeFrames, durationFrames - fadeFrames, durationFrames],
    [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  const audioVolume = interpolate(
    frame,
    [0, fadeFrames, durationFrames - fadeFrames, durationFrames],
    [0, design.audio_gain || 1.4, design.audio_gain || 1.4, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" }
  );

  return (
    <AbsoluteFill style={{ opacity: sceneOpacity }}>
      <AbsoluteFill
        style={{
          background: design.bg_color,
        }}
      />

      {/* Floating background elements */}
      {design.floating_elements && (
        <>
          {[0, 1, 2, 3].map((i) => (
            <FloatingElement
              key={i}
              frame={frame}
              durationFrames={durationFrames}
              index={i}
              color={design.accent_color || "#3b82f6"}
              size={40 + i * 20}
            />
          ))}
          <ShapeAccent
            frame={frame}
            durationFrames={durationFrames}
            color={design.secondary_color || "#1e293b"}
            position="top-right"
          />
          <ShapeAccent
            frame={frame}
            durationFrames={durationFrames}
            color={design.accent_color || "#3b82f6"}
            position="bottom-left"
          />
        </>
      )}

      {/* Image layer */}
      {imageSrc && (
        <ImageLayer
          frame={frame}
          durationFrames={durationFrames}
          imageSrc={imageSrc}
          accentColor={design.accent_color || "#3b82f6"}
          blurStrength={design.blur_strength || 6}
        />
      )}

      {/* Text overlay */}
      <TextOverlay
        text={scene.narration}
        position={design.text_position || "bottom"}
        textColor={design.text_color || "#f8fafc"}
        accentColor={design.accent_color || "#3b82f6"}
        badgeText={`Scene ${scene.scene}`}
        showBadge={design.show_badge !== false}
      />

      {/* Audio */}
      {audioSrc && <Audio src={audioSrc} volume={audioVolume} />}
    </AbsoluteFill>
  );
};

export const VideoEnhanced: React.FC<VideoProps> = ({ scenes, design: designProp }) => {
  const design = parseDesign(designProp);
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: design.bg_color, fontFamily: "Inter, -apple-system, sans-serif" }}>
      {scenes.map((scene) => {
        const startFrame = secondsToFrames(scene.start, fps);
        const durationFrames = Math.max(1, secondsToFrames(scene.duration, fps));
        return (
          <Sequence key={scene.scene} from={startFrame} durationInFrames={durationFrames}>
            <SceneLayer scene={scene} durationFrames={durationFrames} design={design} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

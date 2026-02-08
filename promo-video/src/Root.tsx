import React from "react";
import { Composition, registerRoot, Still } from "remotion";
import { PromoVideo } from "./Video";
import { MockDashboard } from "./MockDashboard";
import { MockMobile } from "./MockMobile";

const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="PromoVideo"
        component={PromoVideo}
        durationInFrames={540}
        fps={30}
        width={1920}
        height={1080}
      />
      <Still
        id="DashboardStill"
        component={MockDashboard}
        width={1920}
        height={1080}
      />
      <Still
        id="MobileStill"
        component={MockMobile}
        width={390}
        height={844}
      />
    </>
  );
};

registerRoot(RemotionRoot);

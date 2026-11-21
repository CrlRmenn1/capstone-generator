import {
  BrainCircuit, ChartColumn, Cpu, Gamepad2, Glasses, Globe, GraduationCap, HeartPulse, Landmark, Layers, Leaf,
  Lock, Siren, Smartphone, Sprout, Store,
} from "lucide-react";

export const AREA_ICONS = {
  web: Globe,
  mobile: Smartphone,
  ai_ml: BrainCircuit,
  iot: Cpu,
  game_dev: Gamepad2,
  data_analytics: ChartColumn,
  cybersecurity: Lock,
  ar_vr: Glasses,
};

export const DOMAIN_ICONS = {
  education: GraduationCap,
  health: HeartPulse,
  agriculture: Sprout,
  lgu: Landmark,
  sme: Store,
  environment: Leaf,
  disaster: Siren,
};

export const iconFor = (map, key) => map[key] || Layers;

import {
  ChartColumn,
  ClipboardList,
  FilePlus,
  Files,
  FlaskConical,
  Folder,
  House,
  Inbox,
  Package,
  Search,
  Settings,
  Timer,
  UserCog,
  Users,
  type LucideIcon,
} from "lucide-react";

const ICONOS: Record<string, LucideIcon> = {
  home: House,
  users: Users,
  "file-plus": FilePlus,
  files: Files,
  search: Search,
  inbox: Inbox,
  flask: FlaskConical,
  clipboard: ClipboardList,
  "user-cog": UserCog,
  package: Package,
  chart: ChartColumn,
  settings: Settings,
  timer: Timer,
  folder: Folder,
};

export function Icono({ nombre, tamano = 18 }: { nombre: string; tamano?: number }) {
  const Componente = ICONOS[nombre] ?? Folder;
  return <Componente size={tamano} strokeWidth={1.8} aria-hidden />;
}

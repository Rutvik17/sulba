// A course's page lists its levels, each level's modules and each module's labs, in the course's
// order. The site stores labs one by one (labs.ts), so the outline is put back together here.
import type { LabEntry } from './labs';

export interface ModuleOutline {
  readonly slug: string;
  readonly title: string;
  readonly labs: readonly LabEntry[];
}

export interface LevelOutline {
  readonly title: string;
  readonly modules: readonly ModuleOutline[];
}

export interface CourseOutline {
  readonly slug: string;
  readonly title: string;
  readonly levels: readonly LevelOutline[];
}

interface Building {
  slug: string;
  title: string;
  levels: { title: string; modules: { slug: string; title: string; labs: LabEntry[] }[] }[];
}

/** Each course, with its labs grouped by level and module, in the course's order. */
export function courseOutlines(labs: readonly LabEntry[]): CourseOutline[] {
  const courses: Building[] = [];
  for (const lab of [...labs].sort((a, b) => a.order - b.order)) {
    const [courseSlug = '', moduleSlug = ''] = lab.path.split('/');
    let course = courses.find((each) => each.slug === courseSlug);
    if (!course) {
      course = { slug: courseSlug, title: lab.course, levels: [] };
      courses.push(course);
    }
    let level = course.levels.at(-1);
    if (level?.title !== lab.level) {
      level = { title: lab.level, modules: [] };
      course.levels.push(level);
    }
    let module = level.modules.at(-1);
    if (module?.slug !== moduleSlug) {
      module = { slug: moduleSlug, title: lab.module, labs: [] };
      level.modules.push(module);
    }
    module.labs.push(lab);
  }
  return courses;
}

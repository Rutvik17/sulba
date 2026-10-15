import { defineCollection } from 'astro:content';
import { z } from 'astro/zod';
import { type LabEntry, labsLoader } from './lib/labs';

export const collections = {
  // Checked when the courses load, so the schema only carries the type.
  labs: defineCollection({ loader: labsLoader(), schema: z.custom<LabEntry>() }),
};

import { type RefObject, useLayoutEffect, useRef } from 'react';
import { I18nProvider } from 'react-aria-components/I18nProvider';
import {
  Slider as AriaSlider,
  type SliderProps as AriaSliderProps,
  Label,
  SliderFill,
  SliderOutput,
  SliderThumb,
  SliderTrack,
} from 'react-aria-components/Slider';
import { classes } from '../classes';
import styles from './slider.module.css';

const css = classes(styles, 'slider', 'header', 'label', 'output', 'track', 'fill', 'thumb');

export interface SliderProps
  extends Omit<AriaSliderProps<number>, 'className' | 'style' | 'children'> {
  /** The slider's visible name, such as "Learning rate". */
  label: string;
  /**
   * How a value is written where formatOptions can't say it, such as a slider through a list of
   * stops, whose value is a stop's place in the list. Screen readers read it too.
   */
  valueText?: (value: number) => string;
}

/**
 * A number chosen by dragging, or with the keys: arrows step, Page Up and Page Down take larger
 * steps, and Home and End reach the ends. formatOptions or valueText sets how the value is written.
 */
export function Slider({ label, valueText, ...props }: SliderProps) {
  const input = useRef<HTMLInputElement>(null);
  return (
    // The site is in English, so a value is written as the page writes numbers: 1.25, not 1,25.
    <I18nProvider locale="en-US">
      <AriaSlider {...props} className={css.slider}>
        {({ state }) => {
          const text = valueText?.(state.getThumbValue(0));
          return (
            <>
              <div className={css.header}>
                <Label className={css.label}>{label}</Label>
                <SliderOutput className={css.output}>{text}</SliderOutput>
              </div>
              <SliderTrack className={css.track}>
                <SliderFill className={css.fill} />
                <SliderThumb className={css.thumb} inputRef={input} />
              </SliderTrack>
              {text !== undefined && <ValueText input={input} text={text} />}
            </>
          );
        }}
      </AriaSlider>
    </I18nProvider>
  );
}

/**
 * Gives the slider's hidden input the value as valueText writes it. React Aria sets the input's
 * aria-valuetext from formatOptions; this runs after it, on every change of value.
 */
function ValueText({ input, text }: { input: RefObject<HTMLInputElement | null>; text: string }) {
  useLayoutEffect(() => {
    input.current?.setAttribute('aria-valuetext', text);
  });
  return null;
}

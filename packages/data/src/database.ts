export type Json = string | number | boolean | null | { [key: string]: Json | undefined } | Json[];

export type Database = {
  public: {
    Tables: {
      attempts: {
        Row: {
          caught: string[] | null;
          checks_passed: number | null;
          checks_total: number | null;
          created_at: string;
          day: string;
          happened_at: string;
          hint: number | null;
          id: string;
          kind: string;
          learner_id: string;
          problems: number | null;
          seconds: number;
          stage_id: string;
          stage_version: string;
          tests_passed: number | null;
          tests_total: number | null;
        };
        ComputedFields: never;
        Insert: {
          caught?: string[] | null;
          checks_passed?: number | null;
          checks_total?: number | null;
          created_at?: string;
          day: string;
          happened_at: string;
          hint?: number | null;
          id: string;
          kind: string;
          learner_id?: string;
          problems?: number | null;
          seconds?: number;
          stage_id: string;
          stage_version: string;
          tests_passed?: number | null;
          tests_total?: number | null;
        };
        Update: {
          caught?: string[] | null;
          checks_passed?: number | null;
          checks_total?: number | null;
          created_at?: string;
          day?: string;
          happened_at?: string;
          hint?: number | null;
          id?: string;
          kind?: string;
          learner_id?: string;
          problems?: number | null;
          seconds?: number;
          stage_id?: string;
          stage_version?: string;
          tests_passed?: number | null;
          tests_total?: number | null;
        };
        Relationships: [];
      };
      progress: {
        Row: {
          caught: string[] | null;
          hints: number;
          learner_id: string;
          passed_at: string | null;
          passed_version: string | null;
          problems: number | null;
          runs: number;
          seconds: number;
          solution_viewed: boolean;
          stage_id: string;
        };
        ComputedFields: never;
        Insert: {
          caught?: string[] | null;
          hints?: number;
          learner_id: string;
          passed_at?: string | null;
          passed_version?: string | null;
          problems?: number | null;
          runs?: number;
          seconds?: number;
          solution_viewed?: boolean;
          stage_id: string;
        };
        Update: {
          caught?: string[] | null;
          hints?: number;
          learner_id?: string;
          passed_at?: string | null;
          passed_version?: string | null;
          problems?: number | null;
          runs?: number;
          seconds?: number;
          solution_viewed?: boolean;
          stage_id?: string;
        };
        Relationships: [];
      };
      study_days: {
        Row: {
          day: string;
          learner_id: string;
          seconds: number;
        };
        ComputedFields: never;
        Insert: {
          day: string;
          learner_id: string;
          seconds?: number;
        };
        Update: {
          day?: string;
          learner_id?: string;
          seconds?: number;
        };
        Relationships: [];
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      close_account: { Args: Record<PropertyKey, never>; Returns: undefined };
    };
    Enums: {
      [_ in never]: never;
    };
    CompositeTypes: {
      [_ in never]: never;
    };
  };
};

type DatabaseWithoutInternals = Omit<Database, '__InternalSupabase'>;

type DefaultSchema = DatabaseWithoutInternals[Extract<keyof Database, 'public'>];

export type Tables<
  DefaultSchemaTableNameOrOptions extends
    | keyof (DefaultSchema['Tables'] & DefaultSchema['Views'])
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Tables'] &
        DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Views'])
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof DatabaseWithoutInternals }
  ? (DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Tables'] &
      DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Views'])[TableName] extends {
      Row: infer R;
    }
    ? R
    : never
  : DefaultSchemaTableNameOrOptions extends keyof (DefaultSchema['Tables'] & DefaultSchema['Views'])
    ? (DefaultSchema['Tables'] & DefaultSchema['Views'])[DefaultSchemaTableNameOrOptions] extends {
        Row: infer R;
      }
      ? R
      : never
    : never;

export type TablesInsert<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema['Tables']
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Tables']
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof DatabaseWithoutInternals }
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Tables'][TableName] extends {
      Insert: infer I;
    }
    ? I
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema['Tables']
    ? DefaultSchema['Tables'][DefaultSchemaTableNameOrOptions] extends {
        Insert: infer I;
      }
      ? I
      : never
    : never;

export type TablesUpdate<
  DefaultSchemaTableNameOrOptions extends
    | keyof DefaultSchema['Tables']
    | { schema: keyof DatabaseWithoutInternals },
  TableName extends DefaultSchemaTableNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Tables']
    : never = never,
> = DefaultSchemaTableNameOrOptions extends { schema: keyof DatabaseWithoutInternals }
  ? DatabaseWithoutInternals[DefaultSchemaTableNameOrOptions['schema']]['Tables'][TableName] extends {
      Update: infer U;
    }
    ? U
    : never
  : DefaultSchemaTableNameOrOptions extends keyof DefaultSchema['Tables']
    ? DefaultSchema['Tables'][DefaultSchemaTableNameOrOptions] extends {
        Update: infer U;
      }
      ? U
      : never
    : never;

export type Enums<
  DefaultSchemaEnumNameOrOptions extends
    | keyof DefaultSchema['Enums']
    | { schema: keyof DatabaseWithoutInternals },
  EnumName extends DefaultSchemaEnumNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions['schema']]['Enums']
    : never = never,
> = DefaultSchemaEnumNameOrOptions extends { schema: keyof DatabaseWithoutInternals }
  ? DatabaseWithoutInternals[DefaultSchemaEnumNameOrOptions['schema']]['Enums'][EnumName]
  : DefaultSchemaEnumNameOrOptions extends keyof DefaultSchema['Enums']
    ? DefaultSchema['Enums'][DefaultSchemaEnumNameOrOptions]
    : never;

export type CompositeTypes<
  PublicCompositeTypeNameOrOptions extends
    | keyof DefaultSchema['CompositeTypes']
    | { schema: keyof DatabaseWithoutInternals },
  CompositeTypeName extends PublicCompositeTypeNameOrOptions extends {
    schema: keyof DatabaseWithoutInternals;
  }
    ? keyof DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions['schema']]['CompositeTypes']
    : never = never,
> = PublicCompositeTypeNameOrOptions extends { schema: keyof DatabaseWithoutInternals }
  ? DatabaseWithoutInternals[PublicCompositeTypeNameOrOptions['schema']]['CompositeTypes'][CompositeTypeName]
  : PublicCompositeTypeNameOrOptions extends keyof DefaultSchema['CompositeTypes']
    ? DefaultSchema['CompositeTypes'][PublicCompositeTypeNameOrOptions]
    : never;

export const Constants = {
  public: {
    Enums: {},
  },
} as const;

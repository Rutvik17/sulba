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
      events: {
        Row: {
          action: string;
          actor_client: string | null;
          actor_id: string | null;
          actor_kind: Database['public']['Enums']['actor_kind'];
          at: string;
          changes: NonNullable<Json>;
          id: number;
          subject_id: string;
          subject_type: string;
          workspace_id: string;
        };
        ComputedFields: never;
        Insert: {
          action: string;
          actor_client?: string | null;
          actor_id?: string | null;
          actor_kind: Database['public']['Enums']['actor_kind'];
          at?: string;
          changes?: NonNullable<Json>;
          id?: never;
          subject_id: string;
          subject_type: string;
          workspace_id: string;
        };
        Update: {
          action?: string;
          actor_client?: string | null;
          actor_id?: string | null;
          actor_kind?: Database['public']['Enums']['actor_kind'];
          at?: string;
          changes?: NonNullable<Json>;
          id?: never;
          subject_id?: string;
          subject_type?: string;
          workspace_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'events_actor_id_fkey';
            columns: ['actor_id'];
            isOneToOne: false;
            referencedRelation: 'people';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'events_workspace_id_fkey';
            columns: ['workspace_id'];
            isOneToOne: false;
            referencedRelation: 'workspaces';
            referencedColumns: ['id'];
          },
        ];
      };
      invitations: {
        Row: {
          created_at: string;
          created_by: string | null;
          expires_at: string;
          id: string;
          role: Database['public']['Enums']['workspace_role'];
          token_hash: string;
          workspace_id: string;
        };
        ComputedFields: never;
        Insert: {
          created_at?: string;
          created_by?: string | null;
          expires_at?: string;
          id?: string;
          role: Database['public']['Enums']['workspace_role'];
          token_hash: string;
          workspace_id: string;
        };
        Update: {
          created_at?: string;
          created_by?: string | null;
          expires_at?: string;
          id?: string;
          role?: Database['public']['Enums']['workspace_role'];
          token_hash?: string;
          workspace_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'invitations_created_by_fkey';
            columns: ['created_by'];
            isOneToOne: false;
            referencedRelation: 'people';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'invitations_workspace_id_fkey';
            columns: ['workspace_id'];
            isOneToOne: false;
            referencedRelation: 'workspaces';
            referencedColumns: ['id'];
          },
        ];
      };
      members: {
        Row: {
          joined_at: string;
          person_id: string;
          role: Database['public']['Enums']['workspace_role'];
          workspace_id: string;
        };
        ComputedFields: never;
        Insert: {
          joined_at?: string;
          person_id: string;
          role: Database['public']['Enums']['workspace_role'];
          workspace_id: string;
        };
        Update: {
          joined_at?: string;
          person_id?: string;
          role?: Database['public']['Enums']['workspace_role'];
          workspace_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'members_person_id_fkey';
            columns: ['person_id'];
            isOneToOne: false;
            referencedRelation: 'people';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'members_workspace_id_fkey';
            columns: ['workspace_id'];
            isOneToOne: false;
            referencedRelation: 'workspaces';
            referencedColumns: ['id'];
          },
        ];
      };
      people: {
        Row: {
          email: string | null;
          id: string;
          name: string;
          updated_at: string;
        };
        ComputedFields: never;
        Insert: {
          email?: string | null;
          id: string;
          name?: string;
          updated_at?: string;
        };
        Update: {
          email?: string | null;
          id?: string;
          name?: string;
          updated_at?: string;
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
      reviews: {
        Row: {
          card_id: string;
          created_at: string;
          id: string;
          learner_id: string;
          rating: number;
          reviewed_at: string;
        };
        ComputedFields: never;
        Insert: {
          card_id: string;
          created_at?: string;
          id: string;
          learner_id?: string;
          rating: number;
          reviewed_at: string;
        };
        Update: {
          card_id?: string;
          created_at?: string;
          id?: string;
          learner_id?: string;
          rating?: number;
          reviewed_at?: string;
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
      workspaces: {
        Row: {
          created_at: string;
          id: string;
          name: string;
          slug: string;
        };
        ComputedFields: never;
        Insert: {
          created_at?: string;
          id?: string;
          name: string;
          slug: string;
        };
        Update: {
          created_at?: string;
          id?: string;
          name?: string;
          slug?: string;
        };
        Relationships: [];
      };
    };
    Views: {
      [_ in never]: never;
    };
    Functions: {
      accept_invitation: { Args: { token: string }; Returns: string };
      close_account: { Args: Record<PropertyKey, never>; Returns: undefined };
      create_invitation: {
        Args: { role: Database['public']['Enums']['workspace_role']; workspace: string };
        Returns: string;
      };
      create_workspace: {
        Args: { name: string; slug: string };
        Returns: {
          created_at: string;
          id: string;
          name: string;
          slug: string;
        };
        SetofOptions: {
          from: '*';
          to: 'workspaces';
          isOneToOne: true;
          isSetofReturn: false;
        };
      };
      delete_workspace: { Args: { workspace: string }; Returns: undefined };
      invitation: {
        Args: { token: string };
        Returns: {
          role: Database['public']['Enums']['workspace_role'];
          workspace_name: string;
        }[];
      };
      remove_member: { Args: { person: string; workspace: string }; Returns: undefined };
      set_member_role: {
        Args: {
          person: string;
          role: Database['public']['Enums']['workspace_role'];
          workspace: string;
        };
        Returns: undefined;
      };
    };
    Enums: {
      actor_kind: 'person' | 'agent' | 'github' | 'system';
      workspace_role: 'viewer' | 'member' | 'admin' | 'owner';
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
    Enums: {
      actor_kind: ['person', 'agent', 'github', 'system'],
      workspace_role: ['viewer', 'member', 'admin', 'owner'],
    },
  },
} as const;

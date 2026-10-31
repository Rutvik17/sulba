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
      criteria: {
        Row: {
          created_at: string;
          id: string;
          number: number;
          spec_id: string;
          suspect_since: string | null;
          text: string;
          updated_at: string;
          workspace_id: string;
        };
        ComputedFields: never;
        Insert: {
          created_at?: string;
          id?: string;
          number: number;
          spec_id: string;
          suspect_since?: string | null;
          text: string;
          updated_at?: string;
          workspace_id: string;
        };
        Update: {
          created_at?: string;
          id?: string;
          number?: number;
          spec_id?: string;
          suspect_since?: string | null;
          text?: string;
          updated_at?: string;
          workspace_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'criteria_workspace_id_spec_id_fkey';
            columns: ['workspace_id', 'spec_id'];
            isOneToOne: false;
            referencedRelation: 'specs';
            referencedColumns: ['workspace_id', 'id'];
          },
        ];
      };
      events: {
        Row: {
          action: string;
          actor_agent: string | null;
          actor_client: string | null;
          actor_id: string | null;
          actor_kind: Database['public']['Enums']['actor_kind'];
          at: string;
          changes: NonNullable<Json>;
          id: number;
          spec_id: string | null;
          subject_id: string;
          subject_type: string;
          workspace_id: string;
        };
        ComputedFields: never;
        Insert: {
          action: string;
          actor_agent?: string | null;
          actor_client?: string | null;
          actor_id?: string | null;
          actor_kind: Database['public']['Enums']['actor_kind'];
          at?: string;
          changes?: NonNullable<Json>;
          id?: never;
          spec_id?: string | null;
          subject_id: string;
          subject_type: string;
          workspace_id: string;
        };
        Update: {
          action?: string;
          actor_agent?: string | null;
          actor_client?: string | null;
          actor_id?: string | null;
          actor_kind?: Database['public']['Enums']['actor_kind'];
          at?: string;
          changes?: NonNullable<Json>;
          id?: never;
          spec_id?: string | null;
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
      questions: {
        Row: {
          answer: string | null;
          answered_at: string | null;
          answered_by: string | null;
          asked_at: string;
          asked_by: string | null;
          asked_by_agent: string | null;
          id: string;
          request_id: string;
          text: string;
          updated_at: string;
          workspace_id: string;
        };
        ComputedFields: never;
        Insert: {
          answer?: string | null;
          answered_at?: string | null;
          answered_by?: string | null;
          asked_at?: string;
          asked_by?: string | null;
          asked_by_agent?: string | null;
          id?: string;
          request_id: string;
          text: string;
          updated_at?: string;
          workspace_id: string;
        };
        Update: {
          answer?: string | null;
          answered_at?: string | null;
          answered_by?: string | null;
          asked_at?: string;
          asked_by?: string | null;
          asked_by_agent?: string | null;
          id?: string;
          request_id?: string;
          text?: string;
          updated_at?: string;
          workspace_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'questions_answered_by_fkey';
            columns: ['answered_by'];
            isOneToOne: false;
            referencedRelation: 'people';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'questions_asked_by_fkey';
            columns: ['asked_by'];
            isOneToOne: false;
            referencedRelation: 'people';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'questions_workspace_id_request_id_fkey';
            columns: ['workspace_id', 'request_id'];
            isOneToOne: false;
            referencedRelation: 'requests';
            referencedColumns: ['workspace_id', 'id'];
          },
        ];
      };
      repositories: {
        Row: {
          added_at: string;
          added_by: string | null;
          branch: string;
          github_id: number | null;
          id: string;
          name: string;
          owner_github_id: number | null;
          workspace_id: string;
        };
        ComputedFields: never;
        Insert: {
          added_at?: string;
          added_by?: string | null;
          branch?: string;
          github_id?: number | null;
          id?: string;
          name: string;
          owner_github_id?: number | null;
          workspace_id: string;
        };
        Update: {
          added_at?: string;
          added_by?: string | null;
          branch?: string;
          github_id?: number | null;
          id?: string;
          name?: string;
          owner_github_id?: number | null;
          workspace_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'repositories_added_by_fkey';
            columns: ['added_by'];
            isOneToOne: false;
            referencedRelation: 'people';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'repositories_workspace_id_fkey';
            columns: ['workspace_id'];
            isOneToOne: false;
            referencedRelation: 'workspaces';
            referencedColumns: ['id'];
          },
        ];
      };
      requests: {
        Row: {
          body: string;
          created_at: string;
          created_by: string | null;
          id: string;
          number: number;
          status: Database['public']['Enums']['request_status'];
          title: string;
          updated_at: string;
          workspace_id: string;
        };
        ComputedFields: never;
        Insert: {
          body?: string;
          created_at?: string;
          created_by?: string | null;
          id?: string;
          number: number;
          status?: Database['public']['Enums']['request_status'];
          title: string;
          updated_at?: string;
          workspace_id: string;
        };
        Update: {
          body?: string;
          created_at?: string;
          created_by?: string | null;
          id?: string;
          number?: number;
          status?: Database['public']['Enums']['request_status'];
          title?: string;
          updated_at?: string;
          workspace_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'requests_created_by_fkey';
            columns: ['created_by'];
            isOneToOne: false;
            referencedRelation: 'people';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'requests_workspace_id_fkey';
            columns: ['workspace_id'];
            isOneToOne: false;
            referencedRelation: 'workspaces';
            referencedColumns: ['id'];
          },
        ];
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
      spec_reviews: {
        Row: {
          answered_at: string | null;
          id: string;
          note: string | null;
          requested_at: string;
          requested_by: string | null;
          reviewer_id: string;
          spec_id: string;
          verdict: Database['public']['Enums']['review_verdict'];
          workspace_id: string;
        };
        ComputedFields: never;
        Insert: {
          answered_at?: string | null;
          id?: string;
          note?: string | null;
          requested_at?: string;
          requested_by?: string | null;
          reviewer_id: string;
          spec_id: string;
          verdict?: Database['public']['Enums']['review_verdict'];
          workspace_id: string;
        };
        Update: {
          answered_at?: string | null;
          id?: string;
          note?: string | null;
          requested_at?: string;
          requested_by?: string | null;
          reviewer_id?: string;
          spec_id?: string;
          verdict?: Database['public']['Enums']['review_verdict'];
          workspace_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'spec_reviews_requested_by_fkey';
            columns: ['requested_by'];
            isOneToOne: false;
            referencedRelation: 'people';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'spec_reviews_reviewer_id_fkey';
            columns: ['reviewer_id'];
            isOneToOne: false;
            referencedRelation: 'people';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'spec_reviews_workspace_id_spec_id_fkey';
            columns: ['workspace_id', 'spec_id'];
            isOneToOne: false;
            referencedRelation: 'specs';
            referencedColumns: ['workspace_id', 'id'];
          },
        ];
      };
      specs: {
        Row: {
          body: string;
          created_at: string;
          created_by: string | null;
          id: string;
          number: number;
          owner_id: string | null;
          request_id: string | null;
          status: Database['public']['Enums']['spec_status'];
          title: string;
          updated_at: string;
          workspace_id: string;
        };
        ComputedFields: never;
        Insert: {
          body?: string;
          created_at?: string;
          created_by?: string | null;
          id?: string;
          number: number;
          owner_id?: string | null;
          request_id?: string | null;
          status?: Database['public']['Enums']['spec_status'];
          title: string;
          updated_at?: string;
          workspace_id: string;
        };
        Update: {
          body?: string;
          created_at?: string;
          created_by?: string | null;
          id?: string;
          number?: number;
          owner_id?: string | null;
          request_id?: string | null;
          status?: Database['public']['Enums']['spec_status'];
          title?: string;
          updated_at?: string;
          workspace_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'specs_created_by_fkey';
            columns: ['created_by'];
            isOneToOne: false;
            referencedRelation: 'people';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'specs_owner_id_fkey';
            columns: ['owner_id'];
            isOneToOne: false;
            referencedRelation: 'people';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'specs_workspace_id_fkey';
            columns: ['workspace_id'];
            isOneToOne: false;
            referencedRelation: 'workspaces';
            referencedColumns: ['id'];
          },
          {
            foreignKeyName: 'specs_workspace_id_request_id_fkey';
            columns: ['workspace_id', 'request_id'];
            isOneToOne: false;
            referencedRelation: 'requests';
            referencedColumns: ['workspace_id', 'id'];
          },
        ];
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
      test_claims: {
        Row: {
          classname: string;
          criterion_number: number;
          file: string | null;
          id: number;
          message: string | null;
          name: string;
          outcome: Database['public']['Enums']['test_outcome'];
          report_id: string;
          spec_number: number;
          workspace_id: string;
        };
        ComputedFields: never;
        Insert: {
          classname?: string;
          criterion_number: number;
          file?: string | null;
          id?: never;
          message?: string | null;
          name: string;
          outcome: Database['public']['Enums']['test_outcome'];
          report_id: string;
          spec_number: number;
          workspace_id: string;
        };
        Update: {
          classname?: string;
          criterion_number?: number;
          file?: string | null;
          id?: never;
          message?: string | null;
          name?: string;
          outcome?: Database['public']['Enums']['test_outcome'];
          report_id?: string;
          spec_number?: number;
          workspace_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'test_claims_workspace_id_report_id_fkey';
            columns: ['workspace_id', 'report_id'];
            isOneToOne: false;
            referencedRelation: 'latest_reports';
            referencedColumns: ['workspace_id', 'id'];
          },
          {
            foreignKeyName: 'test_claims_workspace_id_report_id_fkey';
            columns: ['workspace_id', 'report_id'];
            isOneToOne: false;
            referencedRelation: 'test_reports';
            referencedColumns: ['workspace_id', 'id'];
          },
        ];
      };
      test_reports: {
        Row: {
          branch: string;
          failed: number;
          id: string;
          passed: number;
          received_at: string;
          repository_id: string;
          run_attempt: number;
          run_id: number;
          sha: string;
          skipped: number;
          suite: string;
          tests: number;
          workflow: string;
          workspace_id: string;
        };
        ComputedFields: never;
        Insert: {
          branch: string;
          failed: number;
          id?: string;
          passed: number;
          received_at?: string;
          repository_id: string;
          run_attempt: number;
          run_id: number;
          sha: string;
          skipped: number;
          suite: string;
          tests: number;
          workflow: string;
          workspace_id: string;
        };
        Update: {
          branch?: string;
          failed?: number;
          id?: string;
          passed?: number;
          received_at?: string;
          repository_id?: string;
          run_attempt?: number;
          run_id?: number;
          sha?: string;
          skipped?: number;
          suite?: string;
          tests?: number;
          workflow?: string;
          workspace_id?: string;
        };
        Relationships: [
          {
            foreignKeyName: 'test_reports_workspace_id_repository_id_fkey';
            columns: ['workspace_id', 'repository_id'];
            isOneToOne: false;
            referencedRelation: 'repositories';
            referencedColumns: ['workspace_id', 'id'];
          },
        ];
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
      criterion_proofs: {
        Row: {
          checked_at: string | null;
          criterion_id: string;
          criterion_number: number;
          failed: number | null;
          passed: number | null;
          skipped: number | null;
          spec_id: string;
          spec_number: number;
          spec_owner_id: string | null;
          spec_status: Database['public']['Enums']['spec_status'];
          spec_title: string;
          state: Database['public']['Enums']['proof'] | null;
          suspect_since: string | null;
          tests: number | null;
          text: string;
          workspace_id: string;
        };
        ComputedFields: never;
        Relationships: [
          {
            foreignKeyName: 'criteria_workspace_id_spec_id_fkey';
            columns: ['workspace_id', 'spec_id'];
            isOneToOne: false;
            referencedRelation: 'specs';
            referencedColumns: ['workspace_id', 'id'];
          },
          {
            foreignKeyName: 'specs_owner_id_fkey';
            columns: ['spec_owner_id'];
            isOneToOne: false;
            referencedRelation: 'people';
            referencedColumns: ['id'];
          },
        ];
      };
      latest_claims: {
        Row: {
          classname: string;
          criterion_number: number;
          file: string | null;
          id: number;
          message: string | null;
          name: string;
          outcome: Database['public']['Enums']['test_outcome'];
          received_at: string;
          report_id: string;
          repository: string;
          run_attempt: number;
          run_id: number;
          sha: string;
          spec_number: number;
          suite: string;
          workflow: string;
          workspace_id: string;
        };
        ComputedFields: never;
        Relationships: [];
      };
      latest_reports: {
        Row: {
          branch: string;
          failed: number;
          id: string;
          passed: number;
          received_at: string;
          repository_id: string;
          run_attempt: number;
          run_id: number;
          sha: string;
          skipped: number;
          suite: string;
          tests: number;
          workflow: string;
          workspace_id: string;
        };
        ComputedFields: never;
        Relationships: [
          {
            foreignKeyName: 'test_reports_workspace_id_repository_id_fkey';
            columns: ['workspace_id', 'repository_id'];
            isOneToOne: false;
            referencedRelation: 'repositories';
            referencedColumns: ['workspace_id', 'id'];
          },
        ];
      };
      spec_proofs: {
        Row: {
          criteria: number | null;
          failing: number | null;
          proven: number | null;
          spec_id: string;
          workspace_id: string;
        };
        ComputedFields: never;
        Relationships: [
          {
            foreignKeyName: 'criteria_workspace_id_spec_id_fkey';
            columns: ['workspace_id', 'spec_id'];
            isOneToOne: false;
            referencedRelation: 'specs';
            referencedColumns: ['workspace_id', 'id'];
          },
        ];
      };
    };
    Functions: {
      accept_invitation: { Args: { token: string }; Returns: string };
      add_criterion: { Args: { spec: string; text: string }; Returns: number };
      add_repository: {
        Args: { branch?: string; name: string; workspace: string };
        Returns: string;
      };
      answer_question: { Args: { answer: string; question: string }; Returns: undefined };
      ask_question: { Args: { request: string; text: string }; Returns: string };
      close_account: { Args: Record<PropertyKey, never>; Returns: undefined };
      confirm_criterion: { Args: { criterion: string }; Returns: undefined };
      create_invitation: {
        Args: { role: Database['public']['Enums']['workspace_role']; workspace: string };
        Returns: string;
      };
      create_request: {
        Args: { body?: string; title: string; workspace: string };
        Returns: number;
      };
      create_spec: {
        Args: { criteria?: string[]; request?: string; title: string; workspace: string };
        Returns: number;
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
      record_report: {
        Args: { reports: string[]; run: Json; suite: string; workspace: string };
        Returns: Json;
      };
      remove_member: { Args: { person: string; workspace: string }; Returns: undefined };
      remove_reviewer: { Args: { reviewer: string; spec: string }; Returns: undefined };
      request_review: { Args: { reviewer: string; spec: string }; Returns: undefined };
      review_spec: {
        Args: {
          note?: string;
          spec: string;
          verdict: Database['public']['Enums']['review_verdict'];
        };
        Returns: Database['public']['Enums']['spec_status'];
      };
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
      proof: 'proven' | 'failing' | 'unproven';
      request_status: 'open' | 'planned' | 'closed';
      review_verdict: 'pending' | 'approved' | 'changes_requested';
      spec_status: 'draft' | 'in_review' | 'approved' | 'implemented' | 'abandoned' | 'superseded';
      test_outcome: 'passed' | 'failed' | 'skipped';
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
      proof: ['proven', 'failing', 'unproven'],
      request_status: ['open', 'planned', 'closed'],
      review_verdict: ['pending', 'approved', 'changes_requested'],
      spec_status: ['draft', 'in_review', 'approved', 'implemented', 'abandoned', 'superseded'],
      test_outcome: ['passed', 'failed', 'skipped'],
      workspace_role: ['viewer', 'member', 'admin', 'owner'],
    },
  },
} as const;

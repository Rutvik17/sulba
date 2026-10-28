import {
  holds,
  type Invitation,
  invite,
  invitedRoles,
  joinLink,
  type Member,
  type Role,
  removeMember,
  revokeInvitation,
  roleAbilities,
  roleNames,
  roles,
  setRole,
} from '@sulba/data/workspaces';
import { Button } from '@sulba/ui/button';
import { classes } from '@sulba/ui/classes';
import { Dialog } from '@sulba/ui/dialog';
import { Select } from '@sulba/ui/select';
import { TextField } from '@sulba/ui/textfield';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from '@tanstack/react-router';
import { useState } from 'react';
import { useAccount } from './account';
import { dayOf } from './format';
import { Notice } from './Notice';
import styles from './page.module.css';
import { keys, useInvitations, useMembers } from './queries';
import { useWorkspace } from './Shell';
import { useTitle } from './title';

const css = classes(
  styles,
  'page',
  'header',
  'title',
  'count',
  'section',
  'heading',
  'note',
  'scroll',
  'table',
  'person',
  'name',
  'dim',
  'numeric',
  'actions',
  'link',
  'unseen',
);

const optionsOf = (choices: readonly Role[]) =>
  choices.map((id) => ({ id, name: roleNames[id], description: roleAbilities[id] }));

/**
 * Who is in the workspace and what each may do. Admins change roles, remove people and make
 * invitation links; owners also manage owners. Everyone can leave.
 */
export function Members() {
  const workspace = useWorkspace();
  useTitle('Members', workspace.name);
  const { client, personId } = useAccount();
  const { data: members } = useMembers(workspace);
  const isAdmin = holds(workspace.role, 'admin');
  const isOwner = workspace.role === 'owner';
  const invitations = useInvitations(workspace, isAdmin);
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const [failure, setFailure] = useState<string | null>(null);
  const [removing, setRemoving] = useState<Member | null>(null);
  const [inviting, setInviting] = useState(false);

  const reread = () =>
    Promise.all([
      queryClient.invalidateQueries({ queryKey: keys.members(workspace.id) }),
      queryClient.invalidateQueries({ queryKey: keys.workspace(workspace.slug) }),
      queryClient.invalidateQueries({ queryKey: keys.workspaces }),
    ]);

  const changeRole = useMutation({
    mutationFn: ({ person, role }: { person: string; role: Role }) =>
      setRole(client, workspace.id, person, role),
    onMutate: () => setFailure(null),
    onSuccess: reread,
    onError: (error) => setFailure(error.message),
  });
  const remove = useMutation({
    mutationFn: (member: Member) => removeMember(client, workspace.id, member.personId),
    onMutate: () => setFailure(null),
    onSuccess: async (_, member) => {
      setRemoving(null);
      await reread();
      if (member.personId === personId) await navigate({ to: '/' });
    },
    onError: (error) => {
      setRemoving(null);
      setFailure(error.message);
    },
  });
  const revoke = useMutation({
    mutationFn: (invitation: Invitation) => revokeInvitation(client, invitation.id),
    onMutate: () => setFailure(null),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: keys.invitations(workspace.id) }),
    onError: (error) => setFailure(error.message),
  });

  // Admins manage viewers, members and admins; only owners manage owners.
  const manages = (member: Member) => (member.role === 'owner' ? isOwner : isAdmin);
  const choices = optionsOf(isOwner ? roles : roles.filter((role) => role !== 'owner'));
  const people = members.length === 1 ? '1 person' : `${members.length} people`;

  return (
    <div className={css.page}>
      <header className={css.header}>
        <div>
          <h1 className={css.title}>Members</h1>
          <p className={css.count}>{people}</p>
        </div>
        {isAdmin ? <Button onPress={() => setInviting(true)}>Invite people</Button> : null}
      </header>

      <Notice text={failure} />

      <section className={css.section} aria-labelledby="people">
        <h2 id="people" className={css.heading}>
          People
        </h2>
        <div className={css.scroll}>
          <table className={css.table}>
            <thead>
              <tr>
                <th scope="col">Name</th>
                <th scope="col">Role</th>
                <th scope="col">Joined</th>
                <th scope="col">
                  <span className={css.unseen}>Actions</span>
                </th>
              </tr>
            </thead>
            <tbody>
              {members.map((member) => {
                const self = member.personId === personId;
                const label = member.name || member.email || 'Someone';
                return (
                  <tr key={member.personId}>
                    <td>
                      <span className={css.person}>
                        <span className={css.name}>
                          {label}
                          {self ? <span className={css.dim}> (you)</span> : null}
                        </span>
                        {member.name && member.email ? (
                          <span className={css.dim}>{member.email}</span>
                        ) : null}
                      </span>
                    </td>
                    <td>
                      {manages(member) ? (
                        <Select
                          label={`${label}’s role`}
                          hideLabel
                          size="small"
                          options={choices}
                          value={member.role}
                          onChange={(role) => changeRole.mutate({ person: member.personId, role })}
                          isDisabled={changeRole.isPending}
                        />
                      ) : (
                        roleNames[member.role]
                      )}
                    </td>
                    <td className={css.numeric}>{dayOf(member.joinedAt)}</td>
                    <td className={css.actions}>
                      {self || manages(member) ? (
                        <Button variant="ghost" size="small" onPress={() => setRemoving(member)}>
                          {self ? 'Leave' : 'Remove'}
                        </Button>
                      ) : null}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {isAdmin ? (
        <section className={css.section} aria-labelledby="links">
          <h2 id="links" className={css.heading}>
            Invitation links
          </h2>
          {invitations.data?.length ? (
            <div className={css.scroll}>
              <table className={css.table}>
                <thead>
                  <tr>
                    <th scope="col">Joins as</th>
                    <th scope="col">Made by</th>
                    <th scope="col">Expires</th>
                    <th scope="col">
                      <span className={css.unseen}>Actions</span>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {invitations.data.map((invitation) => (
                    <tr key={invitation.id}>
                      <td>{roleNames[invitation.role]}</td>
                      <td>
                        {invitation.madeBy || <span className={css.dim}>No longer here</span>}
                      </td>
                      <td className={css.numeric}>{dayOf(invitation.expiresAt)}</td>
                      <td className={css.actions}>
                        <Button
                          variant="ghost"
                          size="small"
                          onPress={() => revoke.mutate(invitation)}
                          isDisabled={revoke.isPending}
                        >
                          Revoke
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className={css.note}>
              {invitations.isPending ? '' : 'No open links. A link lasts 7 days.'}
            </p>
          )}
        </section>
      ) : null}

      <Dialog
        title={
          removing?.personId === personId
            ? `Leave ${workspace.name}?`
            : `Remove ${removing?.name || removing?.email || 'them'} from ${workspace.name}?`
        }
        isOpen={removing !== null}
        onOpenChange={(open) => {
          if (!open) setRemoving(null);
        }}
        actions={
          <>
            <Button slot="close" variant="outline">
              Cancel
            </Button>
            <Button
              onPress={() => removing && remove.mutate(removing)}
              isDisabled={remove.isPending}
            >
              {removing?.personId === personId ? 'Leave' : 'Remove'}
            </Button>
          </>
        }
      >
        <p>
          {removing?.personId === personId
            ? 'You lose access at once, and need a new invitation to come back.'
            : 'They lose access at once. You can invite them again.'}
        </p>
      </Dialog>

      <InviteDialog isOpen={inviting} onClose={() => setInviting(false)} />
    </div>
  );
}

/** Makes an invitation link, which is shown once, to copy. */
function InviteDialog({ isOpen, onClose }: { isOpen: boolean; onClose: () => void }) {
  const workspace = useWorkspace();
  const { client } = useAccount();
  const queryClient = useQueryClient();
  const [role, setRoleChoice] = useState<Role>('member');
  const [link, setLink] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const make = useMutation({
    mutationFn: () => invite(client, workspace.id, role),
    onSuccess: async (token) => {
      setLink(joinLink(window.location.origin, token));
      await queryClient.invalidateQueries({ queryKey: keys.invitations(workspace.id) });
    },
  });

  const close = () => {
    onClose();
    setLink(null);
    setCopied(false);
    make.reset();
  };
  const copy = async () => {
    if (!link) return;
    await navigator.clipboard.writeText(link);
    setCopied(true);
  };

  return (
    <Dialog
      title="Invite people"
      isOpen={isOpen}
      onOpenChange={(open) => {
        if (!open) close();
      }}
      actions={
        link ? (
          <Button onPress={close}>Done</Button>
        ) : (
          <>
            <Button slot="close" variant="outline">
              Cancel
            </Button>
            <Button onPress={() => make.mutate()} isDisabled={make.isPending}>
              Create link
            </Button>
          </>
        )
      }
    >
      {link ? (
        <>
          <p>
            Anyone with this link can join {workspace.name} as a {roleNames[role].toLowerCase()} for
            7 days. You won’t see the link again once you close this.
          </p>
          <div className={css.link}>
            <TextField label="Invitation link" value={link} isReadOnly />
          </div>
          <Button variant="outline" onPress={() => void copy()}>
            {copied ? 'Copied' : 'Copy link'}
          </Button>
        </>
      ) : (
        <>
          <p>
            Make a link to share with the people you want in {workspace.name}. Anyone who opens it
            in the next 7 days can join, until you revoke it.
          </p>
          <Select
            label="They join as"
            options={optionsOf(invitedRoles)}
            value={role}
            onChange={setRoleChoice}
          />
          <Notice text={make.error?.message ?? null} />
        </>
      )}
    </Dialog>
  );
}

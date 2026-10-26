import java.lang.reflect.RecordComponent;
import java.time.LocalDate;
import java.time.LocalTime;
import java.time.format.TextStyle;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.stream.Collectors;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.DatabindException;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.exc.ValueInstantiationException;
import tools.jackson.databind.json.JsonMapper;

/** The tools a model calls, each by its name, with its arguments written as JSON text. */
public final class Tools {
    /** What a tool does with its arguments, giving the text the model reads. */
    @FunctionalInterface
    public interface Action<A> {
        String run(A arguments) throws Desk.Refused;
    }

    /** A tool: its name, the record its arguments are read into, an example of them as JSON,
     * and what it does. */
    public record Tool<A extends Record>(String name, Class<A> arguments, String example, Action<A> action) {}

    /** list_tickets's arguments. */
    public record ListTickets(Ticket.Status status) {}

    /** free_times's arguments. */
    public record FreeTimes(Service service, LocalDate day) {}

    private static final JsonMapper JSON = JsonMapper.builder().build();

    private final Map<String, Tool<?>> tools = new LinkedHashMap<>();

    public Tools(List<Tool<?>> tools) {
        for (var tool : tools) {
            if (this.tools.putIfAbsent(tool.name(), tool) != null) {
                throw new IllegalArgumentException("Two tools are named " + tool.name() + ".");
            }
        }
    }

    /** The desk's tools for a model: list_tickets and free_times. */
    public static Tools forDesk(Desk desk) {
        return new Tools(List.of(
                new Tool<>(
                        "list_tickets",
                        ListTickets.class,
                        "{\"status\": \"open\"}",
                        arguments -> desk.listTickets(arguments.status())),
                new Tool<>("free_times", FreeTimes.class, "{\"service\": \"ssa\", \"day\": \"2026-11-03\"}", arguments -> {
                    var times = desk.free(arguments.service(), arguments.day());
                    var when = arguments.day().getDayOfWeek().getDisplayName(TextStyle.FULL, Locale.ENGLISH) + " "
                            + arguments.day();
                    var advisers = "The " + arguments.service().title() + " advisers";
                    return times.isEmpty()
                            ? advisers + " aren't free on " + when + "."
                            : advisers + " are free on " + when + " at "
                                    + times.stream().map(LocalTime::toString).collect(Collectors.joining(", ")) + ".";
                })));
    }

    /** The tools' names, in the order they were given. */
    public List<String> names() {
        return List.copyOf(tools.keySet());
    }

    /** Runs the tool a model called, with the arguments it wrote, and gives the text the model
     * reads: the tool's result, or an error that says how to call again. */
    public String call(String name, String arguments) {
        var tool = tools.get(name);
        if (tool == null) {
            return "Error: there is no tool named \"" + name + "\". The tools are " + String.join(", ", tools.keySet())
                    + ".";
        }
        return call(tool, arguments);
    }

    private static <A extends Record> String call(Tool<A> tool, String arguments) {
        JsonNode given;
        try {
            given = JSON.readTree(arguments.isBlank() ? "{}" : arguments);
        } catch (JacksonException error) {
            given = null;
        }
        if (given == null || !given.isObject()) {
            return "Error: " + tool.name() + "'s arguments are one JSON object, like " + tool.example()
                    + ", and these aren't.";
        }
        var names = Arrays.stream(tool.arguments().getRecordComponents())
                .map(RecordComponent::getName)
                .toList();
        for (var key : given.propertyNames()) {
            if (!names.contains(key)) {
                return "Error: " + tool.name() + " takes no " + key + ". It takes " + String.join(", ", names)
                        + ", like " + tool.example() + ".";
            }
        }
        for (var key : names) {
            if (!given.has(key) || given.get(key).isNull()) {
                return "Error: " + tool.name() + " needs " + key + ". For example: " + tool.example();
            }
        }
        A read;
        try {
            read = JSON.treeToValue(given, tool.arguments());
        } catch (ValueInstantiationException refused) {
            return "Error: " + refused.getCause().getMessage();
        } catch (DatabindException error) {
            var key = error.getPath().getFirst().getPropertyName();
            return "Error: " + key + " can't be " + given.get(key) + ". For example: " + tool.example();
        }
        try {
            return tool.action().run(read);
        } catch (Desk.Refused refused) {
            return "Error: " + refused.getMessage();
        }
    }
}

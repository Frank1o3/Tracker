import math

def get_vel(x1: int | float, y1: int | float, x2: int | float, y2: int | float) -> tuple[int, int]:
    """
    Calculate the velocity components in the x and y directions based on two points 
    and a time interval.

    Args:
        x1 (int | float): The x-coordinate of the starting position.
        y1 (int | float): The y-coordinate of the starting position.
        x2 (int | float): The x-coordinate of the current position.
        y2 (int | float): The y-coordinate of the current position.

    Returns:
        tuple[int, int]: A tuple containing the integer values of velocity in the 
                         x (vx) and y (vy) directions, using floor division.
    """
    vx = math.floor((x2 - x1))
    vy = math.floor((y2 - y1))
    return (vx, vy)


def get_acceleration(v1: int | float, v2: int | float, t: float) -> float:
    """
    Calculate the acceleration given the velocity at two time points.

    Args:
        v1 (int | float): The initial velocity at time t1.
        v2 (int | float): The velocity at time t2.
        t (float): The time difference between the two velocity points.

    Returns:
        float: The estimated acceleration.
    """
    return (v2 - v1) / t if t != 0 else 0


def get_future_position_nl(oldX: int | float, oldY: int | float, CX: int | float, CY: int | float, old_vx: int | float, old_vy: int | float, t: float) -> tuple[int, int]:
    """
    Predict the future position using a quadratic motion model, which accounts for acceleration.

    Args:
        oldX (int | float): The x-coordinate of the previous position.
        oldY (int | float): The y-coordinate of the previous position.
        CX (int | float): The x-coordinate of the current position.
        CY (int | float): The y-coordinate of the current position.
        old_vx (int | float): The previous velocity in the x direction.
        old_vy (int | float): The previous velocity in the y direction.
        t (float): The time interval between the old and current positions.

    Returns:
        tuple[int, int]: The predicted position in x and y as integers.
    """
    # Calculate current velocities
    vx, vy = get_vel(oldX, oldY, CX, CY)

    # Calculate the acceleration in both x and y directions
    ax = get_acceleration(old_vx, vx, t)
    ay = get_acceleration(old_vy, vy, t)

    # Predict the future position using the quadratic motion formula
    newX = math.ceil(CX + vx * t + 0.5 * ax * t**2)
    newY = math.ceil(CY + vy * t + 0.5 * ay * t**2)

    return (newX, newY)

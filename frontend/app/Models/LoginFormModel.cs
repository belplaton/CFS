using System.ComponentModel.DataAnnotations;

namespace Cfs.Frontend.Models;

public sealed class LoginFormModel
{
    [Required]
    [EmailAddress]
    public string Email { get; set; } = "user@cfs.local";

    [Required]
    [MinLength(6)]
    public string Password { get; set; } = "frontend-network";
}

using System.ComponentModel.DataAnnotations;

namespace Cfs.Frontend.Models;

public sealed class CreateFolderFormModel
{
    [Required]
    [StringLength(80, MinimumLength = 2)]
    public string Name { get; set; } = string.Empty;
}

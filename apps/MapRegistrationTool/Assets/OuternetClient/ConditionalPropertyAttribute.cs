using UnityEngine;

public class ConditionalPropertyAttribute : PropertyAttribute
{
    public string propertyName;
    public object value;

    public ConditionalPropertyAttribute(string propertyName, object value)
    {
        this.propertyName = propertyName;
        this.value = value;
    }
}
